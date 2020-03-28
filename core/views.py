from django.shortcuts import render
from django.templatetags.static import static


def home(request):
    return render(request, "core/home.html")


def card_demo(request):
    card = dict(
        title='Tracing DAY-ZERO and Forecasting the Fade out of the COVID-19 Outbreak in Lombardy, Italy: A Compartmental Modelling and Numerical Optimization Approach.',
        date='March 26, 2020',
        description='Objectives: The rapidly evolving coronavirus disease 2019 (COVID-19), was declared a pandemic by the World Health Organization on March 11, 2020. It was first detected in the city of Wuhan in China and has spread globally resulting in substantial health and economic crisis in many countries.',
        pdf='#',
        ext='#',
        img_src=str(static('core/img/paper-sample.png'))
    )
    return render(request, "core/card_demo.html", {'card': card})

def about(request):
    return render(request, "core/about.html")
