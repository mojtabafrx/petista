from django import template
from product.models import Category

register = template.Library()

@register.simple_tag
def make_category(menu_list):
    if menu_list == "__all__":
        category = Category.objects.filter(parent__isnull=True)
    elif isinstance(menu_list, list):
        category = Category.objects.filter(title__in=menu_list)
    else:
        category = Category.objects.filter(title=menu_list)
    string = '<ul class = "navbar-nav me-auto mb-2 mb-lg-0">'
    for category in category:
        string+=backward_tree(category)
    string+="</ul>"
    return string

def backward_tree(category, dropdown=False):
    if category.children.all().count() == 0:
        if dropdown:
            return '<li><a class="dropdown-item" href="#">'+category.title+'</a></li>'
        return '<li class="nav-item"><a class="nav-link" href="#">'+category.title+"</a></li>"
    else:
        string = '<li class="nav-item dropdown"><a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown" aria-haspopup="true" aria-expanded="false">' + category.title + '</a><ul class="dropdown-menu" aria-labelledby="navbarDropdown">'
        for child in category.children.all():
            string+=backward_tree(child, dropdown=True)
        string+="</ul></li>"
        return string


        
