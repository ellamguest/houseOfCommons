#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 21:06:37 2018

@author: emg
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import gender_guesser.detector as gender
from pathlib import Path

"""RESEARCH QUESTIONS
- number of question by gender, between genders
- question topics by gender
- answering speed by asker and answerer gender
- inter party questions?
"""

print('hello9')

def get_current_ministers():
    cabinet_url = 'https://www.gov.uk/government/ministers'
    
    r = requests.get(cabinet_url)
    
    soup = BeautifulSoup(r.content, 'html.parser')
    
    soup.find('a', {'text':"Prime Minister"})
    
    current = soup.find_all('h3', {'class':"current-appointee"})
    
    roles = soup.find_all('p', {'class':'role'})
    
    
    current_ministers = {}
    currents = soup.find_all('h3', {'class':"current-appointee"})
    for current in currents:
        name = current.strong.text
        roles = current.find_next_sibling("p", class_="role")
        for role in roles.find_all('a'):
            current_ministers[role.text] = name
    
    return current_ministers


def clean_role(string):
    drop = ['Lord Chancellor and Secretary of State for',
            'Ministry', 'Office', 'Department',
            'Secretary of State', 'Chancellor', 'State',
            'Minister', 'HM', 'Chief Secretary', 'Leader', 'Affairs', 'Commissioners',
            'Commission', 'President of the Board of Trade', 'Lord Chancellor', 
            'Department', ' of ', ' for ',' the ', ' and ', ' to ']

    for s in drop:
        string=string.replace(s, ' ')
    
    return string.strip()


def clean_dict_keys(d):
    clean_d = {}
    for k,v in d.items():
        clean_k = clean_role(k)
        clean_d[clean_k] = v
    
    return clean_d


def get_answering_names():
    file = Path.cwd().joinpath(*['data','commonsoralquestions.csv'])
    df = pd.read_csv(file)
    positions = df['answering body'].unique()
    clean_positions = [clean_role(x) for x in positions]
    
    current_ministers = get_current_ministers()
    clean_ministers = clean_dict_keys(current_ministers)
    
    missing = []
    position_names = {}
    for x in clean_positions:
        if x in clean_ministers.keys():
            position_names[x] = clean_ministers[x]
        else:
            missing.append(x)
      
    d = {}
    for p in positions:
        for k,v in position_names.items():
            if clean_role(p) == k:
                d[p] = v
    
    return d, missing
    
def first_name(string):
    titles = ['Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Sir']
    names = string.split(' ')
    if names[0] in titles:
        names = names[1:]
    return names[0]

def load_data():
    file = Path.cwd().joinpath(*['data','commonsoralquestions.csv'])
    df = pd.read_csv(file)
    df['date tabled'] = pd.to_datetime(df['date tabled'])
    df['answer date'] = pd.to_datetime(df['answer date'])
    df['response_time'] = (df['answer date'] - df['date tabled']).dt.days

    minister_names, missing = get_answering_names()
    
    df['answering_name'] = df['answering body'].map(lambda x: minister_names[x]
                                                    if x in minister_names.keys()
                                                    else '')

    d = gender.Detector()
    
    df['q_first'] = df['tabling member printed'].apply(lambda x: first_name(x))
    df['a_first'] = df['answering_name'].apply(lambda x: first_name(x))
    
    df['q_gender'] = [d.get_gender(name) for name in df['q_first']]
    df['q_gender'].replace('mostly_male', 'male', inplace=True) # fixing for Chris'
    
    
    women = ['Cat Smith', 'Preet Kaur Gill', 'Jo Platt','Kirstene Hair',
             'Mrs Sheryll Murray','Siobhain McDonagh','Mrs Kemi Badenoch',
             'Tulip Siddiq', 'Rushanara Ali','Mims Davies','Suella Fernandes']
    
    df.loc[df['tabling member printed'].isin(women), 'q_gender'] = 'female'
    df['q_gender'].replace('mostly_female', 'female', inplace=True) # fixing for Chris'
    
    men = ['Glyn Davies','Jamie Stone', 'Sandy Martin', 'Mr Pat McFadden',
           'Chi Onwurah','Jo Swinson', 'Ged Killen', 'Mr Ranil Jayawardena',
           'Zac Goldsmith','Mr Virendra Sharma','Mr Shailesh Vara','Bambos Charalambous',
           'Mr Tanmanjeet Singh Dhesi','Rehman Chishti', 'Royston Smith','Bim Afolami',
           'Kwasi Kwarteng','Rishi Sunak']
    
    df.loc[df['tabling member printed'].isin(men), 'q_gender'] = 'male'
    
    
    df['a_gender'] = [d.get_gender(name) for name in df['a_first']]
    df['a_gender'].replace('mostly_male', 'male', inplace=True) # fixing for Chris Grayling
    
    return df


def stats():
    df = load_data()
    
    df.groupby('q_gender')['response_time'].describe()
    df.groupby('a_gender')['response_time'].describe()
    
    t = gender_counts('commons question time > question type')
    t.plot(kind='bar')
     
    t = gender_counts('question status')
    t.plot(kind='bar')

def gender_counts(variable, normalized=True):
    df = load_data()
    
    return df.groupby(['q_gender','a_gender'])[variable].value_counts(normalize=normalized).unstack()
    
    
    
def new_data():
    url = 'http://lda.data.parliament.uk/commonsoralquestions.html'
    parameter = '_pageSize=value'
    
    pd.read_html(url + parameter)
    
def basic_counts():
    df = load_data()
    
    qgc = df['q_gender'].value_counts()
    print(f"of the {len(df)} questions {qgc['male']} are asked by men and {qgc['female']} by women")
    
    agc = df['a_gender'].value_counts()
    print(f"of the {len(df)} questions {agc['male']} are posed to men and {agc['female']} to women \
                                                                ({agc['unknown']} unknown)")


"""
['Church Commissioners',
 'Department of Health and Social Care',
 'Foreign and Commonwealth',
 'Home',
 'House of Commons Commission',
 'International Trade',
 'Justice',
 'Public Accounts Commission',
 "Speaker's Committee on  Electoral Commission"]
"""

