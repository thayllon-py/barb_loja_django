from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save,post_save, m2m_changed
from barb.models import product

from decimal import Decimal

User = settings.AUTH_USER_MODEL

class CartManager(models.Manager):
    def new_or_get(self, request):
        cart_id = request.session.get("cart_id", None)
        qs = self.get_queryset().filter(id = cart_id)
        print(qs.count())
        if qs.count() == 1:
            new_obj = False
            cart_obj = qs.first()
            if request.user.is_authenticated and cart_obj.user is None:
                try:
                    for y in Cart.objects.all():
                        if y.user == request.user:
                            usuario = y.user
                            cart_atual = y
                except Exception as e:
                    print(e)
                if 'usuario' in locals() or 'usuario' in globals():
                    cart_obj = cart_atual
                else:
                    cart_obj.user = request.user
                    cart_obj.save()
                    print(cart_obj,' - ',cart_obj.user)
        else:
            
            cart_obj = Cart.objects.new(user = request.user)
            
            new_obj = True
            request.session['cart_id'] = cart_obj.id
        return cart_obj, new_obj

    def new(self, user = None):
        user_obj = None
        if user is not None:
            if user.is_authenticated:
                user_obj = user
        return self.model.objects.create(user = user_obj)




class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    products = models.ManyToManyField(product, blank = True)
    subtotal = models.DecimalField(default = 0.00, max_digits=100, decimal_places = 2)
    total = models.DecimalField(default=0.00, max_digits=100, decimal_places=2)
    updated = models.DateTimeField(auto_now=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    objects = CartManager()

    def __str__(self):
        return str(self.id)
        
class Qnty(models.Model):
    cart = models.ForeignKey(Cart,on_delete=models.CASCADE,blank = True)
    products = models.ForeignKey(product, on_delete=models.CASCADE,blank = True)
    qnty = models.IntegerField(default=1)
    total = models.DecimalField(default=0.00, max_digits=1000, decimal_places=2)
    def __str__(self):
        return str(self.id)


def m2m_changed_cart_receiver(sender, instance, action, *args, **kwargs):
  #print(action)
  if action == 'post_add' or action == 'post_remove' or action == 'post_clear':
    # print(instance.products.all())
    products = instance.products.all() 
    total = 0 
    for product in products: 
      total += product.price
    if instance.subtotal != total:
      instance.subtotal = total
      
      instance.save()
    instance.subtotal = total
    instance.save()

m2m_changed.connect(m2m_changed_cart_receiver, sender = Cart.products.through)

def pre_save_cart_receiver(sender, instance, *args, **kwargs):
    if instance.subtotal > 0:
        taxa = Decimal(instance.subtotal) * Decimal(0.06) # 8% de taxa
        instance.total = Decimal(instance.subtotal) + Decimal(taxa)
    else:
        instance.total = 0.00

pre_save.connect(pre_save_cart_receiver, sender = Cart)

