import django

django.setup()

from analyze import PaperAnalyzer

texts = ['Estimation of SARS-CoV-2 Infection Prevalence in Santa Clara County',
         'The COVID-19 pandemic has shown a markedly low proportion of cases among children.',
         'Patients enrolled in this study were all hospitalized with COVID-19 in the Central Hospital of Wuhan']

analyzer = PaperAnalyzer()
rel = analyzer.related('vaccine development?')
print([(r[0].title, r[1]) for r in rel])

