from django import template
from category.models import Category

register = template.Library()

@register.simple_tag
def make_category(menu_list):
    if menu_list == "__all__":
        category = Category.objects.filter(parent__isnull=True)
    elif isinstance(menu_list, list):
        category = Category.objects.filter(title__in=menu_list)
    else:
        category = Category.objects.filter(title=menu_list)
    string = "<ul>"
    for category in category:
        string+=backward_tree(category)
    string+="</ul>"
    return string

def backward_tree(category):
    if category.children.all().count() == 0:
        return "<li>"+category.title+"</li>"
    else:
        string = "<ul>"
        string+="<li>"+category.title+"</li>"
        for child in category.children.all():
            string+=backward_tree(child)
        string+="</ul>"
        return string