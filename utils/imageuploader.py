import mimetypes
import os
import uuid
from datetime import datetime


def upload_product_image(instance, filename):
    # mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
    mimetype = filename.split('.')[-1]
    path = "products/" + datetime.now().strftime("%Y/%m/%d")
    os.makedirs(path, exist_ok=True)
    dir = path + "/" + uuid.uuid4().hex + "." + mimetype
    print(dir)
    return dir

def upload_image(instance, filename):
    pass


def make_image_function(name):
    def upload_image(instance, filename):

        # mimetype = mimetypes.guess_type(filename)[0] or 'application/octet-stream'
        mimetype = filename.split('.')[-1]
        path = name  + "/" + datetime.now().strftime("%Y/%m/%d")
        os.makedirs(path, exist_ok=True)
        dir = path + "/" + uuid.uuid4().hex + "." + mimetype
        print(dir)
        return dir
    return upload_image
