from django.db import models


class ConvoTemplate(models.Model):
    name = models.CharField(max_length=100)
    initial_screen = models.ForeignKey(
        'ConvoScreen', null=True, blank=True, on_delete=models.SET_NULL, related_name='initial_for')


class ConvoScreen(models.Model):
    template = models.ForeignKey(
        ConvoTemplate, on_delete=models.CASCADE, related_name='screens')
    id_name = models.CharField(max_length=100)
    custom_dialog_text = models.TextField()
    stop_conversation = models.BooleanField(default=False)


class ConvoOption(models.Model):
    screen = models.ForeignKey(
        ConvoScreen, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    next_screen = models.ForeignKey(
        'ConvoScreen', null=True, blank=True, on_delete=models.SET_NULL, related_name='previous_options')
