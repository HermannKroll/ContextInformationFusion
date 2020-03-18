import argparse

# Init Argparse
parser = argparse.ArgumentParser(description='convert the mysql dump of semmed to postgressql')
parser.add_argument('input', nargs='?', help='input mysql semmed statement')
parser.add_argument('output', nargs='?', help='output filename for all insert-postgresql statements')

args = parser.parse_args()
input = args.input
output = args.output


print("converting mysql input {} into postgresql {} ...".format(input, output))
inFile = open(input, 'r')
outFile = open(output, 'w')


print("start reading input sql file...")
i = 0
for line in inFile:
    # remove all non-insert statements
    if not line.startswith("INSERT"):
        continue
    # Insert-statement must be CREATE TABLE GENERIC_CONCEPT
    # INSERT INTO `PREDICATION` VALUES  -> INSERT INTO PREDICATION VALUES
    insertSplit = line.split('(', 1) # first split
    # Remove ever ` in the first part
    insertSplit[0] = insertSplit[0].replace('`', '')

    # Another Problem: ' in text, its in mysql \' escaped. Postgresql needs ''
    # This must be checked recursivly because \\'' must be also replaced
    while '\\\'' in insertSplit[1]:
        insertSplit[1] = insertSplit[1].replace('\\\'', '\'\'')

    # Second Problem: \" is not valid in postgresql
    while '\\\"' in insertSplit[1]:
        insertSplit[1] = insertSplit[1].replace('\\\"', '')

    # Third Problem: \\ is not valid in postgresql
    while '\\\\' in insertSplit[1]:
        insertSplit[1] = insertSplit[1].replace('\\\\', '\\')

    # Write Statement to file and add the splitted '('
    outFile.write(insertSplit[0] + '(' + insertSplit[1])

    if i % 10000 == 0:
        print("Processed {} lines...".format(i))

    i = i + 1

outFile.close()

print("conversion finished!")


