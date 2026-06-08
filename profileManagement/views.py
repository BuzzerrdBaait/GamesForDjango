#BlazingSugarCookies Profile Management

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Count

from django.conf import settings
from django.core.mail import send_mail
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

import json
import logging
from django.utils import timezone

from .forms import Registration
from .models import userProfile, FriendRequest, Message, UserOptions


def _fmt_ts(dt):
    """Return time-only string if today, otherwise include date."""
    local = timezone.localtime(dt)
    today = timezone.localtime(timezone.now()).date()
    if local.date() == today:
        return local.strftime('%H:%M')
    return local.strftime('%b %d, %H:%M')

User = get_user_model()
logger = logging.getLogger(__name__)

_DEFAULT_HIDDEN_CATEGORY_NAMES = {
    'test',
    'new',
    'newnew',
    'temp',
    'sample',
    'dummy',
    'untitled',
}


def _get_store_nav_context(next_url=''):
    """Build shared store-style nav context for auth pages."""
    from storeFront.models import Category, Product

    hidden_names = {
        str(name).strip().lower()
        for name in getattr(
            settings,
            'STOREFRONT_HIDDEN_CATEGORY_NAMES',
            _DEFAULT_HIDDEN_CATEGORY_NAMES,
        )
        if str(name).strip()
    }

    categories_qs = Category.objects.filter(products__isnull=False).distinct()
    for name in hidden_names:
        categories_qs = categories_qs.exclude(name__iexact=name)

    category_links = list(
        categories_qs
        .order_by('name')
    )
    return {
        'category_links': category_links,
        'on_sale_products': Product.objects.filter(isOnSale=True).exists(),
        'next': next_url,
    }

@login_required
def userProfileHome(request):
    # Import Orders model from storeFront app
    from storeFront.models import Orders, OrderItem, OrderParcelInformation

    # Get user's orders, newest first
    user_orders = Orders.objects.filter(user=request.user).order_by('-created_on')

    # Prepare orders with their items and shipping info
    orders_data = []
    for order in user_orders:
        order_items = OrderItem.objects.filter(order=order)
        parcel_info = OrderParcelInformation.objects.filter(order=order)
        orders_data.append({
            'order': order,
            'items': order_items,
            'parcel_info': parcel_info
        })

    # Friend / social context
    accepted_requests = FriendRequest.objects.filter(
        Q(sender=request.user) | Q(receiver=request.user),
        status='accepted'
    ).select_related('sender', 'receiver')

    friends = []
    for fr in accepted_requests:
        friend = fr.receiver if fr.sender == request.user else fr.sender
        friends.append({'id': friend.pk, 'username': friend.username})

    pending_incoming = FriendRequest.objects.filter(
        receiver=request.user, status='pending'
    ).select_related('sender').order_by('-created_at')

    pending_data = [
        {'id': fr.pk, 'sender_id': fr.sender.pk, 'sender_username': fr.sender.username}
        for fr in pending_incoming
    ]

    # Get or create user options
    user_opts, _ = UserOptions.objects.get_or_create(user=request.user)

    context = {
        'greeting': f"Welcome, {request.user.username}!",
        'orders_data': orders_data,
        'has_orders': user_orders.exists(),
        'friends': friends,
        'pending_requests': pending_data,
        'pending_count': len(pending_data),
        'user_timezone': user_opts.timezone,
        'user_theme': user_opts.color_theme,
        'user_time_format': user_opts.time_format,
        'user_language': user_opts.language,
    }

    return render(request, 'userProfile.html', context)


# ─────────────────────────────────────────────────────────────────────────────
# Friend system API views
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def search_users(request):
    """Live user search by username — returns JSON."""
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})

    users = userProfile.objects.filter(
        username__icontains=q
    ).exclude(pk=request.user.pk)[:10]

    # Current friends
    accepted = FriendRequest.objects.filter(
        Q(sender=request.user, status='accepted') |
        Q(receiver=request.user, status='accepted')
    ).values_list('sender_id', 'receiver_id')
    friend_ids = set()
    for s, r in accepted:
        friend_ids.add(s)
        friend_ids.add(r)
    friend_ids.discard(request.user.pk)

    # Pending sent by me
    pending_sent = set(
        FriendRequest.objects.filter(
            sender=request.user, status='pending'
        ).values_list('receiver_id', flat=True)
    )

    results = []
    for u in users:
        if u.pk in friend_ids:
            relationship = 'friend'
        elif u.pk in pending_sent:
            relationship = 'pending'
        else:
            relationship = 'none'
        results.append({'id': u.pk, 'username': u.username, 'relationship': relationship})

    return JsonResponse({'results': results})


@login_required
@require_POST
def send_friend_request(request):
    """Send a friend request to another user."""
    try:
        data = json.loads(request.body)
        receiver_id = int(data.get('receiver_id', 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if receiver_id == request.user.pk:
        return JsonResponse({'error': 'Cannot add yourself.'}, status=400)

    receiver = get_object_or_404(userProfile, pk=receiver_id)

    existing = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user)
    ).first()

    if existing:
        if existing.status == 'accepted':
            return JsonResponse({'error': 'Already friends.'}, status=400)
        if existing.status == 'pending':
            return JsonResponse({'error': 'Request already pending.'}, status=400)
        if existing.status == 'declined':
            existing.status = 'pending'
            existing.sender = request.user
            existing.receiver = receiver
            existing.save()
            return JsonResponse({'success': True})

    FriendRequest.objects.create(sender=request.user, receiver=receiver)
    return JsonResponse({'success': True})


@login_required
@require_POST
def respond_friend_request(request, request_id):
    """Accept or decline a friend request directed at the current user."""
    fr = get_object_or_404(FriendRequest, pk=request_id, receiver=request.user, status='pending')

    try:
        data = json.loads(request.body)
        action = data.get('action')
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if action == 'accept':
        fr.status = 'accepted'
        fr.save()
        return JsonResponse({'success': True, 'action': 'accepted',
                             'friend': {'id': fr.sender.pk, 'username': fr.sender.username}})
    if action == 'decline':
        fr.status = 'declined'
        fr.save()
        return JsonResponse({'success': True, 'action': 'declined'})

    return JsonResponse({'error': 'Invalid action.'}, status=400)


@login_required
@require_POST
def remove_friend(request, user_id):
    """Remove an existing friendship."""
    other = get_object_or_404(userProfile, pk=user_id)
    FriendRequest.objects.filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user),
        status='accepted'
    ).delete()
    return JsonResponse({'success': True})


# ─────────────────────────────────────────────────────────────────────────────
# Messaging API views
# ─────────────────────────────────────────────────────────────────────────────

@login_required
def get_conversation(request, user_id):
    """Return the message thread between the current user and a friend."""
    other = get_object_or_404(userProfile, pk=user_id)

    is_friend = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user),
        status='accepted'
    ).exists()
    if not is_friend:
        return JsonResponse({'error': 'Not friends.'}, status=403)

    # Mark incoming messages as read
    Message.objects.filter(
        sender=other, receiver=request.user, is_read=False
    ).update(is_read=True)

    messages = Message.objects.filter(
        Q(sender=request.user, receiver=other) |
        Q(sender=other, receiver=request.user)
    ).order_by('timestamp')[:200]

    results = [{
        'id': m.pk,
        'sender_username': m.sender.username,
        'content': m.content,
        'timestamp': _fmt_ts(m.timestamp),
        'is_mine': m.sender_id == request.user.pk,
    } for m in messages]

    return JsonResponse({'messages': results, 'other_username': other.username})


@login_required
@require_POST
def send_message(request):
    """Send a message to a friend."""
    try:
        data = json.loads(request.body)
        receiver_id = int(data.get('receiver_id', 0))
        content = data.get('content', '').strip()
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    if not content:
        return JsonResponse({'error': 'Message cannot be empty.'}, status=400)
    if len(content) > 2000:
        return JsonResponse({'error': 'Message too long (max 2000 chars).'}, status=400)

    receiver = get_object_or_404(userProfile, pk=receiver_id)

    is_friend = FriendRequest.objects.filter(
        Q(sender=request.user, receiver=receiver) |
        Q(sender=receiver, receiver=request.user),
        status='accepted'
    ).exists()
    if not is_friend:
        return JsonResponse({'error': 'Not friends.'}, status=403)

    msg = Message.objects.create(sender=request.user, receiver=receiver, content=content)
    return JsonResponse({'success': True, 'message': {
        'id': msg.pk,
        'sender_username': msg.sender.username,
        'content': msg.content,
        'timestamp': _fmt_ts(msg.timestamp),
        'is_mine': True,
    }})

@login_required
def get_unread_count(request):
    """Return total unread message count and a breakdown by sender."""
    unread = (
        Message.objects
        .filter(receiver=request.user, is_read=False)
        .values('sender_id')
        .annotate(count=Count('id'))
    )
    by_sender = {str(row['sender_id']): row['count'] for row in unread}
    total = sum(by_sender.values())
    return JsonResponse({'total': total, 'by_sender': by_sender})


@login_required
@require_POST
def save_options(request):
    """Save timezone and/or color_theme for the current user."""
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid request.'}, status=400)

    opts, _ = UserOptions.objects.get_or_create(user=request.user)

    valid_timezones    = [c[0] for c in UserOptions.TIMEZONE_CHOICES]
    valid_themes       = [c[0] for c in UserOptions.THEME_CHOICES]
    valid_time_formats = [c[0] for c in UserOptions.TIME_FORMAT_CHOICES]
    valid_languages    = [c[0] for c in UserOptions.LANGUAGE_CHOICES]

    tz = data.get('timezone')
    if tz is not None:
        if tz not in valid_timezones:
            return JsonResponse({'error': 'Invalid timezone.'}, status=400)
        opts.timezone = tz

    theme = data.get('color_theme')
    if theme is not None:
        if theme not in valid_themes:
            return JsonResponse({'error': 'Invalid theme.'}, status=400)
        opts.color_theme = theme

    fmt = data.get('time_format')
    if fmt is not None:
        if fmt not in valid_time_formats:
            return JsonResponse({'error': 'Invalid time format.'}, status=400)
        opts.time_format = fmt

    lang = data.get('language')
    if lang is not None:
        if lang not in valid_languages:
            return JsonResponse({'error': 'Invalid language.'}, status=400)
        opts.language = lang

    opts.save()
    return JsonResponse({'success': True, 'timezone': opts.timezone, 'color_theme': opts.color_theme, 'time_format': opts.time_format, 'language': opts.language})


def loginUser(request):
    """
    Authenticate a user via username + password.
    Supports ``?next=`` so ``@login_required`` redirects work correctly.
    On success, redirects to *next* (if safe) or the store home page.
    """
    # Where to go after a successful login
    next_url = request.GET.get('next', request.POST.get('next', ''))

    # Nav context (same categories the storeFront header uses)
    nav_ctx = _get_store_nav_context(next_url)

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect(reverse('ilovecookbooks:cookbook_list'))
        else:
            return render(request, 'loginPage.html', {
                **nav_ctx,
                'error_message': 'Invalid username or password.',
            })

    return render(request, 'loginPage.html', nav_ctx)
    
def registration(request):
    #This creates a user model based on the User_Profile model which is the base User model extended.

    # Nav context (same categories the storeFront header uses)
    nav_ctx = _get_store_nav_context()

    if request.method == 'POST':
        form = Registration(request.POST)
        if form.is_valid():
            user_data = form.cleaned_data
            new_user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
            )

            try:

                registration_link = request.build_absolute_uri(
                    reverse('profileManagement:authenticate_user', args=[str(new_user.authentication_link)])

                )

                send_mail(
                    f"Welcome {new_user.username}",
                    f"Welcome to BlazingSugarCookies!Here is how to get registered: Below is your authentication key. Copy this:{new_user.authentication_key} Click the link below to complete your registration:{registration_link}",
                    settings.DEFAULT_FROM_EMAIL,
                    [new_user.email],
                    fail_silently=False,
                )

            except Exception as error:
            
                logger.error(f"Sending registration email failed: {error}")

            return redirect('profileManagement:loginUser')

        #end if
    else:
        form = Registration()
    #end if
    return render(request, 'registration.html', {**nav_ctx, 'form': form})


def logoutUser(request):
    """
    Log the current user out and redirect to the store home page.
    Only accepts POST to prevent CSRF logout attacks via GET requests.
    """
    if request.method != 'POST':
        from django.http import HttpResponseNotAllowed
        return HttpResponseNotAllowed(['POST'])
    logout(request)
    return redirect(reverse('storeFront:storeHome'))


def authenticate_user(request, authentication_link):
    """Verify a user's account via the emailed authentication link."""
    user = get_object_or_404(User, authentication_link=authentication_link)

    if user.is_verified == 'Y':
        return redirect(reverse('profileManagement:loginUser'))

    if request.method == 'POST':
        submitted_key = request.POST.get('authentication_key', '')
        if submitted_key == user.authentication_key:
            user.is_verified = 'Y'
            user.save()
            return redirect(reverse('profileManagement:loginUser'))
        else:
            return render(request, 'registration.html', {
                'error_message': 'Invalid authentication key.',
                'show_verification': True,
                'authentication_link': authentication_link,
            })

    return render(request, 'registration.html', {
        'show_verification': True,
        'authentication_link': authentication_link,
    })
