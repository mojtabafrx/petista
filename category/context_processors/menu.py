def menu_context(request):
    if request.user.is_authenticated:
        return {"menu_list" : "__all__"}
    else:
        return {"menu_list" : "home"}