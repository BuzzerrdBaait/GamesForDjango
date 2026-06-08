from django.shortcuts import render



def menu(request):

    greeting = "Welcome "

    return render(request, 'menu/home.html', {
        # This is where you can pass any data you want to the template. You can access it in the template like {{ variable_name }}
        'greeting': greeting,
    })

