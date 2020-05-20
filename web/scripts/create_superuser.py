if __name__ == '__main__':
    import django

    django.setup()

    from django.contrib.auth import get_user_model
    import os

    try:
        username = os.environ['SUPERUSER_USERNAME']
        password = os.environ['SUPERUSER_PASSWORD']
        email = os.environ['SUPERUSER_EMAIL']

        User = get_user_model()

        try:
            user = User.objects.get(username=username)
            print("Tried to create user", username, "but he already exists.")
        except User.DoesNotExist:
            User.objects.create_superuser(username, email, password)
            print("Superuser", username ,"created")

    except KeyError:
        print("[Error] Environment variables not configured correctly. ")