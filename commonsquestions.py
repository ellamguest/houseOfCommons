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


#
"""RESEARCH QUESTIONS
- number of question by gender, between genders
- question topics by gender
- answering speed by asker and answerer gender
- inter party questions?
"""

print('hello7')

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
    drop = ['Ministry of', 'Office', 'Department for',
            'Secretary of State for', 'Chancellor of the', 'Minister of State for',
            'Minister for', 'HM', 'Chief Secretary to', 'Leader of', 'the']

    for s in drop:
        string=string.replace(s, '')
    
    return string.strip()


def clean_dict_keys(d):
    clean_d = {}
    for k,v in d.items():
        clean_k = clean_role(k)
        clean_d[clean_k] = v
    
    return clean_d


def get_answering_names():
    df = pd.read_csv('/Users/emg/Programming/GitHub/net-play/commonsoralquestions.csv')
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

def load_data():
    df = pd.read_csv('/Users/emg/Programming/GitHub/net-play/commonsoralquestions.csv')
    df['date tabled'] = pd.to_datetime(df['date tabled'])
    df['answer date'] = pd.to_datetime(df['answer date'])
    df['response_time'] = (df['answer date'] - df['date tabled']).dt.days
    
    return df
    
def first_name(string):
    titles = ['Mr', 'Mrs', 'Miss', 'Ms', 'Dr', 'Sir']
    names = string.split(' ')
    if names[0] in titles:
        names = names[1:]
    return names[0]

def get_gendered_data():
    df = load_data()

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
    df = get_gendered_data()
    
    df.groupby('q_gender')['response_time'].mean()
    df.groupby('a_gender')['response_time'].mean()
    
    (df.groupby(['q_gender','a_gender'])['q_first'].count()
                                                    .sort_values(ascending=False)
                                                    .unstack())




