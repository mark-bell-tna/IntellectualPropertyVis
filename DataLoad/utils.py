#!/usr/bin/python

import numpy as np
from operator import itemgetter
import re
from collections import OrderedDict

def add_to_dict(D, k, v=1):
    if k in D:
        D[k] += v
    else:
        D[k] = v
        
def find_sequence(B, in_A):

    return [(i, i+len(B)) for i in range(len(in_A)) if in_A[i:i+len(B)] == B]
    
def trunc_array_values(values, decs=0):
    return np.trunc(values*10**decs)/(10**decs)
    
def split_string(text):

    return re.findall(r"[\w|']+|[.,!?;:-]", text)
    

def sort_dict(D):

    new_D = OrderedDict()

    for x in sorted([(k,v) for k,v in D.items()], key=itemgetter(1), reverse=True):
        new_D[x[0]] = x[1]

    return new_D
    
    
class TextForm:

    def __init__(self, text, case_sensitive=True):

        self.text = text
        if case_sensitive:
            self.set_text_form(text)
        else:
            self.set_text_form(text.lower())

    def set_text_form(self, text):

        self.text_form = []

        for c in text:
            ord_c = ord(c)

            if 48 <= ord_c <= 57:
                this_form = '9'
            elif 65 <= ord_c <= 90:
                this_form = 'A'
            elif 97 <= ord_c <= 122:
                this_form = 'a'
            else:
                this_form = c

            if len(self.text_form) == 0:
                self.text_form.append([this_form,1])
                continue
            last_form = self.text_form[-1]
            if last_form[0] == this_form[0]:
                last_form[1] += 1
            else:
                self.text_form.append([this_form, 1])


    def __repr__(self):

        return self.text_form

    def __str__(self):

        return self.get_form_regex()

    def get_form_list(self):

        return self.text_form

    def get_form_regex(self, multi=None):

        out_form = ""

        for f in self.text_form:
            out_form += f[0]

            if f[1] > 1:
                if multi is None:
                    out_form +=  "{" + str(f[1]) + "}"
                else:
                    out_form += "{" + multi + "}"

        return out_form



if __name__ == '__main__':
    
    X = "st paul's cathedral"
    print(split_string(X))