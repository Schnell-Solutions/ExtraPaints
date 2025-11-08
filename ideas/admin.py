from django.contrib import admin

from ideas.models import Tag, Idea, Category, IdeaImage, SavedIdea

admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Idea)
admin.site.register(IdeaImage)
admin.site.register(SavedIdea)

