import django

django.setup()

import analyze

texts = ['Estimation of SARS-CoV-2 Infection Prevalence in Santa Clara County',
         'The COVID-19 pandemic has shown a markedly low proportion of cases among children.',
         'Patients enrolled in this study were all hospitalized with COVID-19 in the Central Hospital of Wuhan']

analyzer = analyze.get_topic_assignment_analyzer()
analyzer.preprocess()
analyzer.assign_to_topics()

