from django.db import models


class ConvoTemplate(models.Model):
    name = models.CharField(max_length=255)
    stf_mode = models.BooleanField(default=False)
    initial_screen = models.ForeignKey(
        'ConvoScreen', null=True, blank=True, on_delete=models.SET_NULL, related_name='initial_for')


class ConvoScreen(models.Model):
    template = models.ForeignKey(
        ConvoTemplate, on_delete=models.CASCADE, related_name='screens')
    id_name = models.CharField(max_length=255)
    custom_dialog_text = models.TextField()
    leftDialog = models.CharField(max_length=255, blank=True)
    stop_conversation = models.BooleanField(default=False)


class ConvoOption(models.Model):
    screen = models.ForeignKey(
        ConvoScreen, on_delete=models.CASCADE, related_name='options')
    text = models.CharField(max_length=255)
    stfReference = models.CharField(max_length=255, blank=True)
    next_screen = models.ForeignKey(
        ConvoScreen, null=True, blank=True, on_delete=models.SET_NULL, related_name='previous_options')
