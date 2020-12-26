file_name = "esc.txt"
out_file = "ESC-classes.txt"

recorded = set()
classes = []

def getKey(item):
    return item[0]

for line in open(file_name, 'r').read().splitlines():
    if(',' in line):
        index, cl = line.split(',')
        if index not in recorded:
            classes.append((int(index), cl))
            recorded.add(index)
classes = sorted(classes, key=getKey)
of = open(out_file, 'w')
for i, c in classes:
    of.write(c + "\n")
of.close()