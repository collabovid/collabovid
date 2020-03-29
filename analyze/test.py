import django

django.setup()

from analyze import compute_topic_score, doc_similarity, calculate_paper_matrix, related, assign_to_topics

texts = ['Estimation of SARS-CoV-2 Infection Prevalence in Santa Clara County',
         'The COVID-19 pandemic has shown a markedly low proportion of cases among children.',
         'Patients enrolled in this study were all hospitalized with COVID-19 in the Central Hospital of Wuhan']

#calculate_paper_matrix()
assign_to_topics()
#rel = related('vaccine development?')
#print([(r[0].title, r[1]) for r in rel])

