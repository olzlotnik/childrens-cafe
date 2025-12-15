def cart_context(request):
    try:
        # Просто получаем корзину из сессии
        cart = request.session.get('cart', {})
        cart_count = sum(cart.values()) if cart else 0
        
        return {
            'cart_count': cart_count
        }
    except Exception as e:
        print(f"Error in cart_context: {e}")
        return {'cart_count': 0}