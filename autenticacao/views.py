from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.models import User
from django.contrib.messages import constants
from django.contrib import messages
from django.contrib import auth
import os
from django.conf import settings
from hashlib import sha256
from autenticacao.utils import password_is_valid, email_html
from .models import Ativacao


def cadastro(request):
    if request.method == 'GET':
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'cadastro.html')
    elif request.method == 'POST':
        usuario = request.POST.get('usuario')
        email = request.POST.get('email')
        senha = request.POST.get('senha')
        confirmar_senha = request.POST.get('confirmar_senha')
        if not password_is_valid(request, senha, confirmar_senha):
            messages.add_message(request, constants.ERROR,
                                 'Informe dados válidos, por favor!')
            return redirect('cadastro')
        try:
            user = User.objects.create_user(username=usuario,
                                            email=email,
                                            password=senha,
                                            is_active=False)
            user.save()
            token = sha256(f'{usuario}{email}'.encode()).hexdigest()
            ativacao = Ativacao(token=token, user=user)
            ativacao.save()
            
            path_template = os.path.join(settings.BASE_DIR, 'autenticacao/templates/emails/cadastro_confirmado.html')
            email_html(path_template, 'Cadastro confirmado', [email,], username=usuario, link_ativacao=f"127.0.0.1:8000/auth/ativar_conta/{token}")

            messages.add_message(request, constants.SUCCESS,
                                 'Usuário cadastrado com sucesso!')

            return redirect('logar')
        except:
            return redirect('cadastro')


def logar(request):
    if request.method == "GET":
        if request.user.is_authenticated:
            return redirect('/')
        return render(request, 'logar.html')
    elif request.method == "POST":
        usuario = request.POST.get('usuario')
        senha = request.POST.get('senha')
        usuario = auth.authenticate(username=usuario, password=senha)
        if not usuario:
            messages.add_message(request, constants.ERROR,
                                 'Usuário ou senha inválidos.')
            return redirect('logar')
        else:
            auth.login(request, usuario)
            return redirect('/')


def sair(request):
    auth.logout(request)
    return redirect('logar')


def ativar_conta(request, token):
    token = get_object_or_404(Ativacao, token=token)
    if token.ativo:
        messages.add_message(request, constants.WARNING, 'Esse token já foi usado')
        return redirect('logar')
    user = User.objects.get(username=token.user.username)
    user.is_active = True
    user.save()
    token.ativo = True
    token.save()
    messages.add_message(request, constants.SUCCESS, 'Conta ativa com sucesso')
    return redirect('logar')