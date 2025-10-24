from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class CustomUserManager(BaseUserManager):
    def create_user(self, siape, nome_completo, email=None, password=None, **extra_fields):
        """
        Cria um usuário. E-mail é opcional.
        Se não houver e-mail, cria um temporário baseado no SIAPE.
        """
        if not siape:
            raise ValueError('O SIAPE é obrigatório')
        
        # Se não tem e-mail, cria um temporário
        if not email:
            email = f"sem.email.{siape}@temporario.inss.gov.br"
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            siape=siape,
            nome_completo=nome_completo,
            **extra_fields
        )
        
        # Define senha aleatória se não fornecida
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()  # Usuário não pode logar sem senha
        
        user.save(using=self._db)
        return user

    def create_superuser(self, email, siape, nome_completo, password=None, **extra_fields):
        """Superusuário DEVE ter e-mail real"""
        if not email:
            raise ValueError('Superusuário deve ter e-mail')
        
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(siape, nome_completo, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        unique=True, 
        verbose_name="E-mail",
        blank=True,  # ← PERMITE VAZIO
        null=False   # ← Mas não NULL no banco (usa string vazia ou temporário)
    )
    siape = models.CharField(
        max_length=15, 
        unique=True,
        verbose_name="SIAPE"
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        blank=True,
        null=True,
        verbose_name="CPF"
    )
    nome_completo = models.CharField(max_length=255, verbose_name="Nome Completo")
    gex = models.CharField(max_length=100, blank=True, null=True, verbose_name="GEX")
    lotacao = models.CharField(max_length=100, blank=True, null=True, verbose_name="Lotação")
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['siape', 'nome_completo']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'

    def __str__(self):
        return f"{self.nome_completo} ({self.siape})"
    
    @property
    def tem_email_real(self):
        """Verifica se o usuário tem um e-mail real (não temporário)"""
        return not self.email.startswith('sem.email.') and '@temporario.inss.gov.br' not in self.email
    
    @property
    def cadastro_completo(self):
        """Verifica se o cadastro está completo"""
        return self.tem_email_real and self.cpf
    
    @property
    def status_cadastro(self):
        """Retorna o status do cadastro"""
        if self.cadastro_completo:
            return "Completo"
        
        problemas = []
        if not self.tem_email_real:
            problemas.append("sem e-mail")
        if not self.cpf:
            problemas.append("sem CPF")
        
        return f"Incompleto ({', '.join(problemas)})"


class EmailServidor(models.Model):
    siape = models.CharField(
        max_length=15, 
        unique=True, 
        verbose_name="SIAPE"
    )
    email = models.EmailField(unique=True, verbose_name="E-mail")
    
    class Meta:
        verbose_name = 'Email de Servidor'
        verbose_name_plural = 'Emails de Servidores'
    
    def __str__(self):
        return f"{self.siape} - {self.email}"