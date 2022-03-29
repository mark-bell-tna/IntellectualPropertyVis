#!/usr/bin/python3

import sys
import numpy as np
import random
from utils import trunc_array_values, add_to_dict, TextForm
from collections import OrderedDict
import json
import os
from time import time_ns
from hashlib import md5

#GP.add_filter('12')

class Entry:

    IDX_POS = 0
    TOKEN_POS = 1
    FORM_1_POS = 2
    FORM_2_POS = 3
    LABEL_POS = 4
    
    def __init__(self, **metadata):  #reference, from_date, to_date):

        self.metadata = metadata
        #self.reference = reference
        #self.from_date = from_date
        #self.to_date = to_date
        self.items = []
        self.predictions = []
    
    def set_reference(self, reference):
        
        self.metadata['reference'] = reference
        
    def get_reference(self):
        
        if 'reference' in self.metadata:
            return self.metadata['reference']
        return None
        
    def hash(self):
        return md5(" ".join(self.get_tokens()).encode('utf-8')).hexdigest()
        
    def get_tokens(self):
        
        return [x[1] for x in self.items]
        
    def get_metadata_row(self):
        
        entry_row = ["ENTRYSTART"]
        for k,v in self.metadata.items():
            entry_row.append(str(k) + ":" + str(v))
        return "|".join(entry_row)
        
    def __hash__(self):  # not consistent
        
        return hash(" ".join(self.get_tokens()))
        
    def merge(self, other, this_priority=True):
        # Use to update one with label/predictions of the other
        
        #merged_entry = Entry(self.reference, self.from_date, self.to_date)
        merged_entry = Entry(**self.metadata)
        
        if this_priority:
            primary = self
            secondary = other
        else:
            primary = other
            secondary = self
        
        for i in range(primary.length()):
            if primary.items[i] != '':
                merged_item = primary.items[i]
            else:
                merged_item = secondary.items[i]
            if primary.predictions[i] is not None:
                merged_prediction = primary.predictions[i]
            else:
                merged_prediction = secondary.predictions[i]
            merged_entry.add_item(merged_item, merged_prediction)
            
        return merged_entry
        
    def add_token(self, token, token_type=''):
        
        TF = TextForm(token)
        t_form = TF.get_form_regex(multi="*")
        t_form_q = TF.get_form_regex()
        self.add_item([len(self.items), token.lower(), t_form, t_form_q, token_type])

    def add_item(self, item, prediction = None):

        self.items.append(item)
        self.predictions.append(prediction)
        
    def set_prediction(self, index, prediction):
        
        #print('P1:',prediction)
        self.predictions[index] = prediction
        #print('P2:', trunc_array_values(self.predictions[index],3))
        
    def length(self):
        
        return len(self.items)
    
    def write_to_file(self, file_handle):
        
        #file_handle.write(":".join(["CATREF", self.reference, self.from_date, self.to_date]) + "\n")
        file_handle.write(self.get_metadata_row() + "\n")
        for i,item in enumerate(self.items):
            output_values = item
            if self.predictions[i] is not None:
                output_values += self.predictions[i]
                
            file_handle.write("|".join([str(x) for x in output_values]) + "\n")
            
    def __iter__(self):

        for item in self.items:

            yield item

        #yield "||||END|1.0"

class TrackTag:

    def __init__(self, tag, min_length, max_length):

        self.tag_name = tag
        self.min_length = min_length
        self.max_length = max_length
        self.tag_start = "B-" + self.tag_name
        self.tag_other = "I-" + self.tag_name
        self.word_buffer = []
        self.is_tag = False
        self.tag_value = []

    def reset(self):

        self.word_buffer = []
        self.is_tag = False
        self.tag_value = []

    def new_word(self, word, tag):

        self.tag_value = []
        self.is_tag = False
        if self.tag_start == tag:
            self.word_buffer = [[word, 1.0, self.tag_start]]
        else:
            if self.tag_other == tag:
                self.word_buffer.append([word, 1.0, self.tag_other])
            else:
                if self.min_length <= len(self.word_buffer) <= self.max_length:
                    self.is_tag = True
                    self.tag_value = self.word_buffer
                    self.word_buffer = [[word, 1.0, tag]]
                else:
                    pass
        #if self.tag_name == "FLD":
        #    if word == "item" or word == "format":
        #        print(word,tag_probabilities)
        #        if self.tag_start in tag_probabilities:
        #            print("Has start tag:", self.tag_start, tag_probabilities[self.tag_start])
        #    print(word,self.word_buffer)

    # deprecated
    def get_tag_probability(self):
        prob = 1
        for t in self.tag_value:
            if t[2] == self.tag_start or t[2] == self.tag_other:
                prob *= t[1]
            else:
                prob *= 1-t[1]
        return prob
        
class WordFile:

    def __init__(self, filename):

        self.filename = filename
        if not os.path.isfile(filename):
            self.file = open(filename,'w')
            self.file.close()
        self.file = open(filename, "r")
        self.catref_positions = []
        self.catref_index = {}
        self.random_mode = False
        self.seed = time_ns()
        self.index_file()
        self.clear_year_filter()

        self.done = set([-1])
        self.reset_iter(True)
        self.iter_pos = -1
        self.start_time = time_ns()

    def set_year_filter(self, from_year, to_year):
        
        self.year_filter = [from_year, to_year]
        
    def clear_year_filter(self):
        
        self.year_filter = [None, None]
        
    def length(self):
        return len(self.catref_positions)
        
    def index_file(self):

        self.file.seek(0)

        line = self.file.readline()
        while line:
            if line.startswith("ENTRYSTART|"):
                fields = dict([l.split(":") for l in line.split("|")[1:]])
                reference = fields['reference']
                self.catref_index[reference] = len(self.catref_positions)
                cur_pos = self.file.tell()-len(line)
                self.catref_positions.append(cur_pos)
            line = self.file.readline()
        self.catref_positions.append(self.file.tell())

    def set_one_hot(self, one_hot_map):
        
        self.one_hot_map = one_hot_map
        self.ids_to_labels = dict([(v,k) for k,v in one_hot_map.items()])
        
    def set_access(self, random_mode=False, sample_size=-1, seed=None):

        if sample_size > 0:
            self.sample_size = sample_size
        else:
            self.sample_size = len(self.catref_positions)
            
        if seed is not None:
            self.seed = seed
        self.random_mode = random
        
    def get_entry(self, reference):
        if reference not in self.catref_index:
            return None
        start_entry = self.catref_positions[self.catref_index[reference]]
        end_entry = self.catref_positions[self.catref_index[reference]+1]
        
        return self.read_entry(start_entry, end_entry)
        
    def read_entry(self, start_entry, end_entry):
        self.file.seek(start_entry)
        line = self.file.readline()
        metadata_row = line[:-1].split("|")
        entry_metadata = dict([m.split(":") for m in metadata_row[1:]])
        #reference = entry_metadata[1]
        #from_date = entry_metadata[2]
        #to_date = entry_metadata[3]
        #E = Entry(reference=reference, from_date=from_date, to_date=to_date)
        E = Entry(**entry_metadata)
        line = self.file.readline()
        while line:
            cur_pos = self.file.tell()-len(line)
            if cur_pos >= end_entry:
                break
            fields = line[:-1].split("|")
            try:
                fields[0] = int(fields[0])
            except:
                print("Error:",fields,":",E.metadata)
                return
            item = fields[:5]
            prediction = fields[5:]
            if len(prediction) == 0:
                prediction = None
            else:
                prediction = [float(p) if p.replace('.','',1).isdigit() else p for p in prediction]
            E.add_item(item, prediction)
            line = self.file.readline()
            
        return E
        

    def it_has_more(self):

        if self.random_mode:
            #if len(self.iter_positions) > self.sample_size:
            #    return True
            if len(self.iter_positions) == 0:
                return False
            if len(self.done) < min(self.sample_size+1,len(self.catref_positions)):
                return True
        else:
            if self.iter_pos < len(self.catref_positions)-2:
                return True
        return False

    def reset_iter(self, full_reset=False):
        
        self.iter_pos = -1
        self.done = set()
        self.iter_positions = [x for x in range(len(self.catref_positions)-1)]
        if full_reset:
            if self.random_mode:
                self.seed = random.randint(1,1000000+(time_ns()-self.start_time))
        #print(self.iter_pos, self.seed)

    def __iter__(self):

        self.reset_iter()
        random.seed(self.seed)
        while self.it_has_more():
            if self.random_mode:
                self.iter_pos = self.iter_positions.pop(random.randint(0, len(self.iter_positions)-1))
                #while self.iter_pos in self.done:
                #    self.iter_pos = random.randint(0,len(self.catref_positions)-2)
                self.done.add(self.iter_pos)
            else:
                self.iter_pos += 1

            start_entry = self.catref_positions[self.iter_pos]
            end_entry = self.catref_positions[self.iter_pos+1]

            E = self.read_entry(start_entry, end_entry)
            
            #if self.year_filter[0] is not None:
            #    try:
            #        this_from = int(E.from_date[0:4])
            #    except:
            #        print(E.from_date, E.reference)
            #    this_to = int(E.to_date[0:4])
            #    if this_from >= self.year_filter[0] and this_to <= self.year_filter[1]:
            #        pass
            #    else:
            #        continue

            yield E

    def words_to_json(self, json_file, tag_types):
        # tag_types should be [Name, min_len, max_len]
        field_names = {}
        entry_dict = {}
        tracker_lookup = {}

        for t in tag_types:
            tracker = TrackTag(t[0], t[1], t[2])
            tracker_lookup[tracker.tag_name] = tracker

        #WF = WordFile("test_words.psv")
        #WF = WordFile(DATA_FOLDER + "copy1_words_1872_updated.psv")
        for entry in self:
            catref = entry.metadata['reference']
            from_date = entry.metadata['from_date']
            to_date = entry.metadata['to_date']
            entry_dict[catref] = {'catalogue_from_date':from_date, 'catalogue_to_date':to_date}
            word_buffer = []
            field_buffer = []
            this_field_name = "FIELD_1"
            ref_dict = entry_dict[catref]            
            for t in tag_types:
                tracker_lookup[t[0]].reset()

            for i,fields in enumerate(entry):
                word = fields[1]
                word_buffer.append(word)
                wd_form_m = fields[2]
                wd_form_q = fields[3]
                #print(fields)
                wd_class = fields[4]

                for tag, tracker in tracker_lookup.items():
                    tracker.new_word(word, wd_class)

                    if tracker.is_tag:
                        if tracker.tag_name == "FLD":
                            field_text = " ".join([w for w in word_buffer[:-len(tracker.tag_value)-1]])
                            field_name = " ".join([w[0] for w in tracker.tag_value])
                            ref_dict[this_field_name] = field_text
                            add_to_dict(field_names, field_name)
                            this_field_name = field_name
                            word_buffer = [word_buffer[-1]]
                        else:
                            start_tag = "<" + tracker.tag_name + ">"
                            end_tag = "</" + tracker.tag_name + ">"
                            word_buffer.insert(-len(tracker.tag_value)-1, start_tag)
                            word_buffer.insert(-1, end_tag)
                    
            #if "format" in word_buffer or "format" in tracker.tag_value:
            #    print("*****Remaining:",word_buffer,"T:",tracker.tag_value, "W:", tracker.word_buffer)
            if len(word_buffer)-len(tracker.tag_value) == 0:
                this_field_name = " ".join([w[0] for w in tracker.tag_value])
            field_text = " ".join([w for w in word_buffer])
            ref_dict[this_field_name] = field_text
        
        print("Fields found:", field_names)

        json.dump(entry_dict, open(json_file, "w"))
        
    def merge_to_file(self, other, out_file, union, has_precedence=True):
        
        # union = merge behaviour; if not union the intersect
        # has_precedence => records for self are used ahead of other if catref in both
        
        self_catrefs = set([k for k in self.catref_index])

        other_catrefs = set([k for k in other.catref_index])
        if union:
            print("Using union")
            all_catrefs = self_catrefs.union(other_catrefs)
        else:
            print("Using intersect")
            all_catrefs = self_catrefs.intersection(other_catrefs)
        
        out_file = open(out_file, 'w')
        
        for cat in all_catrefs:
            if has_precedence:
                primary = self.get_entry(cat)
                secondary = other.get_entry(cat)
            else:
                primary = other.get_entry(cat)
                secondary = self.get_entry(cat)
            
            if primary is None:
                this_entry = secondary
            elif secondary is None:
                this_entry = primary
            else:
                this_entry = primary.merge(secondary)
            #if has_precedence:
            #    if cat in self_catrefs:
            #        this_entry = self.get_entry(cat)
            #    else:
            #        this_entry = other.get_entry(cat)
            #else:
            #    if cat in other_catrefs:
            #        this_entry = other.get_entry(cat)
            #    else:
            #        this_entry = self.get_entry(cat)
            
            
            this_entry.write_to_file(out_file)
            
        out_file.close()
        

if __name__ == '__main__':

    WF1 = WordFile("../Data/GT/BT_43_address_ground_truth.psv")
    WF2 = WordFile("../Data/Temporary/BT_43_predicted.psv")
    out_file = "../Data/Temporary/merge_entries.psv"
    WF1.merge_to_file(WF2, out_file, True, True)
    #E = Entry(reference="A", date="2012")
    #E = Entry(**{'reference':'A', 'date':'2012'})
    #print(E.get_metadata_row())
    #WF_A = WordFile("../Data/Source/BT_43_words.psv")
    #WF_A.set_year_filter(1872, 1872)
    #out_file = open("../Data/1872/BT_43_1872_words.psv", "w")
    #for E in WF_A:
    #    E.write_to_file(out_file)
    #out_file.close()
    #WF_A = WordFile("../Data/Labelled/BT43_test.psv")
    #WF_B = WordFile("../Data/Labelled/BT43_test.1.psv")
    #out_file = "../Data/Temporary/merge_entries.psv"
    #WF_A.merge_to_file(WF_B, out_file, True, True)
    #WF.set_access(random_mode=True)
    #WF.words_to_json("../Data/Labelled/BT43_test.json", [["FLD",2,10]])
    #test_file = open("../Data/Temporary/write_entry.psv","w")
    #WF = WordFile("../Data/1872/test_COPY_1_1872_words.psv")
    #E = WF.get_entry("BT 43/30/252927")
    #E.write_to_file(test_file)
    #test_file.close()
    
    #WF = WordFile("../Data/Source/BT_43_words.psv")
    #for E in WF:
    #    print(E.reference, E.from_date, E.to_date)
    #    for e in E:
    #        print(e)
    #    break
