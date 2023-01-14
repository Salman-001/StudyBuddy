from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q
from .models import Room, Topic, Message, User
from .forms import RoomForm, MessageForm, UserForm, MyUserCreationForm


# Create your views here.

# rooms = [
#     {'id': 1, 'name': 'Lets learn Python!'},
#     {'id': 2, 'name': 'Design with me'},
#     {'id': 3, 'name': 'Frontend Developers'},
# ]

# login view
def loginPage(request):
    page = 'login'

    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':

        # get the username and password from html
        email = request.POST.get('email').lower()
        password = request.POST.get('password')

        # checks if the user exists
        try:
            user = User.objects.get(email=email)
        except:
            messages.error(request, 'User does not exist')

        # check if the user's info are correct
        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Username or Password does not exist')

    context = {'page': page}
    return render(request, 'base/login_register.html', context)


# logout view
def logoutPage(request):
    logout(request)
    return redirect('home')


# register signup view
def registerPage(request):
    form = MyUserCreationForm()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)
            user.username = user.username.lower()
            user.save()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'error occurred during registration')

    return render(request, 'base/login_register.html', {'form': form})


# home view
def home(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''

    # we use two underscore __ in order to move upwards to the parent // icontains to make capital case-insensitive
    rooms = Room.objects.filter(
        Q(topic__name__icontains=q) |
        Q(name__icontains=q) |
        Q(description__icontains=q)
    )

    topics = Topic.objects.all()[0:5]
    room_count = rooms.count()
    room_messages = Message.objects.filter(Q(room__topic__name__icontains=q))

    context = {'rooms': rooms, 'topics': topics,
               'room_count': room_count, 'room_messages': room_messages}
    return render(request, 'base/home.html', context)


# room view
def room(request, pk):
    room = Room.objects.get(id=pk)

    # for many to one relation we use example_set
    room_messages = room.message_set.all()

    # for many to many we can just use .all without underscore
    participants = room.participants.all()

    if request.method == 'POST':
        message = Message.objects.create(
            user=request.user,
            room=room,
            body=request.POST.get('body')
        )
        room.participants.add(request.user)
        return redirect('room', pk=room.id)

    context = {'room': room, 'room_messages': room_messages, 'participants': participants}
    return render(request, 'base/room.html', context)


# user profile
def userProfile(request, pk):
    user = User.objects.get(id=pk)
    rooms = user.room_set.all()
    room_messages = user.message_set.all()
    topics = Topic.objects.all()

    context = {'user': user, 'rooms': rooms,
               'room_messages': room_messages, 'topics': topics}
    return render(request, 'base/profile.html', context)


@login_required(login_url='login')
def updateProfile(request):
    user = request.user
    form = UserForm(instance=user)

    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES, instance=user)

        if form.is_valid():
            form.save()
            return redirect('user-profile', pk=user.id)

    context = {'form': form}
    return render(request, 'base/profile-form.html', context)


# create room view
@login_required(login_url='login')
def createRoom(request):
    onCreate = True
    form = RoomForm()

    topics = Topic.objects.all()

    if request.method == 'POST':
        topic_name = request.POST.get('topic')

        # if the topic name is not found, it will be created
        topic, create = Topic.objects.get_or_create(name=topic_name)

        Room.objects.create(
            host=request.user,
            topic=topic,
            name=request.POST.get('name'),
            description=request.POST.get('description')
        )
        return redirect('home')

    context = {'form': form, 'topics': topics, 'onCreate': onCreate}
    return render(request, 'base/room_form.html', context)


# update / edit room view
@login_required(login_url='login')
def updateRoom(request, pk):
    room = Room.objects.get(id=pk)
    form = RoomForm(instance=room)
    topics = Topic.objects.all()

    if request.user != room.host:
        return HttpResponse('You cannot edit room you don\'t own!')

    if request.method == 'POST':
        topic_name = request.POST.get('topic')
        topic, created = Topic.objects.get_or_create(name=topic_name)
        room.name = request.POST.get('name')
        room.topic = topic
        room.description = request.POST.get('description')
        room.save()
        return redirect('home')

    context = {'form': form, 'topics': topics, 'room': room}
    return render(request, 'base/room_form.html', context)


# delete room view
@login_required(login_url='login')
def deleteRoom(request, pk):
    room = Room.objects.get(id=pk)

    if request.user != room.host:
        return HttpResponse('You cannot delete room you don\'t own!')

    if request.method == 'POST':
        room.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': room})


# update / edit message view
@login_required(login_url='login')
def updateMessage(request, pk):
    msg = Message.objects.get(id=pk)
    form = MessageForm(instance=msg)

    room_name = msg.room

    room = Room.objects.get(name=room_name)

    if request.user != msg.user:
        return HttpResponse('You cannot edit message you don\'t own!')

    if request.method == 'POST':
        form = MessageForm(request.POST, instance=msg)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect("/room/{id}/".format(id=room.id))

    context = {'form': form}
    return render(request, 'base/message_form.html', context)


# delete message view
@login_required(login_url='login')
def deleteMessage(request, pk):
    msg = Message.objects.get(id=pk)

    if request.user != msg.user:
        return HttpResponse('You cannot delete message you don\'t own!')

    if request.method == 'POST':
        msg.delete()
        return redirect('home')

    return render(request, 'base/delete.html', {'obj': msg})


def topicsPage(request):
    q = request.GET.get('q') if request.GET.get('q') != None else ''
    topics = Topic.objects.filter(name__icontains=q)

    context = {'topics': topics}
    return render(request, 'base/topics.html', context)


def activityPage(request):
    room_messages = Message.objects.all()

    context = {'room_messages': room_messages}
    return render(request, 'base/activity.html', context)
