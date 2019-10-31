import sys, json

values = json.load(sys.stdin)['values']
for value in values:
  print str(value['device']) + ':' + str(value['ip'])

