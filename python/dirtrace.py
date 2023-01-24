filename = None
paths = (None, None)
f = '/k/t2.t'
list_of_d = []
counter = {'/': {'k': {'l': {'t.t': {}}}}}
#counter["/"] = {}
import os
while f != '/':
    f, fp = os.path.split(f)
    if filename is not None:
        list_of_d.append(fp)
    if filename is None:
        filename = fp
    
    print(f)
print(list_of_d)
list_of_d.reverse()
for index, d in enumerate(list_of_d):
    print(counter)
    if index == 0:
        if d not in counter["/"].keys():
            counter["/"][d] = {}
        if index == len(list_of_d) - 1:
            counter["/"][d][filename] = {'r1':[12, "", "data_is"]} 

    else:
        prev_dir = list_of_d[index-1]
        if index - 1 == 0:
            if d not in counter["/"][prev_dir]:
                counter["/"][prev_dir][d] = {}
                if index == len(list_of_d) - 1:
                    counter["/"][prev_dir][d][filename] = {'r1':[2, "", "data_is"]} 

#check 1st index - if dir not exists add, if file not exists add under this dir - 0 index
#check next index and put this dir under that

print(counter)