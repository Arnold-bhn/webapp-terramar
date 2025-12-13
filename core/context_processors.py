from .models import Marca, ConfiguracionVisual

def informacion_marca(request):
    """
    Busca la MARCA ACTIVA y su CONFIGURACIÓN VISUAL (Navidad, Verano, etc.)
    para inyectarla en el HTML.
    """
    marca = Marca.objects.filter(activo=True).first()
    
    ctx = {
        'MARCA': marca,
        'COLOR_PRINCIPAL': '#003366', # Default Azul
        'COLOR_SECUNDARIO': '#FF6B4A', # Default Naranja
        'TEMA_CSS': 'DEFAULT',
        'MENSAJE_TOP': ''
    }

    if marca:
        # Buscamos si hay un tema visual activo (Navidad, etc)
        tema = ConfiguracionVisual.objects.filter(marca=marca, activo=True).first()
        if tema:
            ctx['COLOR_PRINCIPAL'] = tema.color_principal
            ctx['COLOR_SECUNDARIO'] = tema.color_secundario
            ctx['TEMA_CSS'] = tema.efecto_especial
            ctx['MENSAJE_TOP'] = tema.mensaje_barra

    return ctx