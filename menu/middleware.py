class ForceSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            # Принудительно создаем сессию для каждого пользователя
            if not request.session.session_key:
                request.session.create()
                request.session.modified = True
                print("ForceSessionMiddleware - Created new session")
            
            # Убедимся, что сессия сохранена
            if not request.session.session_key:
                request.session.save()
            
            response = self.get_response(request)
            return response
        except Exception as e:
            print(f"Error in ForceSessionMiddleware: {e}")
            return self.get_response(request)