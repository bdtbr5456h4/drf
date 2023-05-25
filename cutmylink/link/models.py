from django.db import models

class Click(models.Model):
    ip = models.CharField(max_length=15)
    provider = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    os = models.CharField(max_length=255)
    browser = models.CharField(max_length=255)
    referer = models.CharField(max_length=255)
    link = models.ForeignKey('Link', on_delete=models.CASCADE, null=False)
    device = models.CharField(max_length=255)
    time_create = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.ip

class Link(models.Model):
    url = models.CharField(max_length=21,unique=True)
    redirect_url = models.CharField(max_length=255,default="https://google.com")
    user = models.ForeignKey('User', on_delete=models.CASCADE, null=False, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.url

class User(models.Model):
    telegram_id = models.IntegerField(unique=True)

    def __str__(self):
        return "Tg id: "+ str(self.telegram_id)