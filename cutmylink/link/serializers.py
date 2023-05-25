from rest_framework import serializers

from link.models import Click, Link, User


class ClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = Click
        fields = '__all__'

class LinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = Link
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'