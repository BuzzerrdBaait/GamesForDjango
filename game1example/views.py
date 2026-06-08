from django.shortcuts import render


def game1example(request):

    greeting = "game1example"

    return render(request, 'game1example.html', {
        # This is where you can pass any data you want to the template. You can access it in the template like {{ variable_name }}
        'greeting': greeting,
    })
