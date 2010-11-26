from django.db import models

class Author(models.Model):

        first_name = models.CharField(max_length = 128)
        last_name = models.CharField(max_length = 128)


class Book(models.Model):

    author = models.ManyToManyField(Author)
    title = models.CharField(max_length = 128)
    isbn = models.PositiveIntegerField(unique=True)

class Shelf(models.Model):

    label = models.CharField(blank = True, max_length = 64)
    book = models.ForeignKey(Book)


class Bookmark(models.Model):

    book = models.ForeignKey(Book)
    color = models.IntegerField(choices = (
           (1, 'red'),
           (2, 'green'),
           (3, 'blue')
        ) )

class Chapter(models.Model):

    book = models.ForeignKey(Book)
    page = models.PositiveIntegerField()
    title = models.CharField(max_length = 128)
    contents = models.TextField()





