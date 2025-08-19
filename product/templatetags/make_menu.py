from django import template
from django.urls import reverse
from django.utils.safestring import mark_safe

from product.models import Category

register = template.Library()

menu_template = """
<li>
<div class="item" style="background-image: url('{}')">
            <div class="text">{}</div>
</div>
"""


@register.simple_tag
def make_category(menu_list="__all__"):
    if menu_list == "__all__":
        category = Category.objects.filter(parent__isnull=True)
    elif isinstance(menu_list, list):
        category = Category.objects.filter(title__in=menu_list)
    else:
        category = Category.objects.filter(title=menu_list)
    string = ''
    for category in category:
        string += backward_tree(category)
    # if User.objects.get(username="admin").is_staff:
    # if User.is_authenticated:
    #     my_text = "پنل کاربری"
    #     string += f'<a href="{reverse("user_panel:dashboard")}"><li><div class="item" style="background-image: url("/media/images/account.svg"><div class="text">{my_text}</div></div></li></a>'
    #
    return mark_safe(string)


def backward_tree(category, dropdown=False):
    try:
        img_url = category.image.url
    except:
        img_url = "https://picsum.photos/300/300"
    if category.children.all().count() == 0:
        if dropdown:
            # return '<li><a class="dropdown-item" href="#">'+category.title+'</a></li>'
            my_href = reverse("product:product_list_by_category", kwargs={"category_slug": category.slug})
            return f'<a href="{my_href}">' + menu_template.format(img_url, category.title) + "</a></li>"
        return menu_template.format(img_url, category.title) + "</li>"
    else:
        for child in category.children.all():
            string = menu_template.format(img_url, category.title) + '<ul class="sub-menu">'
            string += backward_tree(child, dropdown=True)
        string += "</ul></li>"
        return string


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
