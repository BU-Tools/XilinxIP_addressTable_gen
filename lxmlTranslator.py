from lxml import etree
import argparse
from os import path

spirit = '{http://www.spiritconsortium.org/XMLSchema/SPIRIT/1685-2009}'
permissionMap = {'read-only': 'r', 'read-write': 'rw'}


def elementParser(element, attrDict=None):
    # initialize attrDict
    if attrDict is None:
        attrDict = {}

    # parse every child element into attrDict
    if element.find(spirit+'name') is not None:
        attrDict['id'] = element.find(spirit+'name').text.upper()
    if element.find(spirit+'addressOffset') is not None:
        attrDict['address'] = element.find(spirit+'addressOffset').text

    # mask
    if element.find(spirit+'bitWidth') is not None:
        attrDict['bitWidth'] = int(element.find(spirit+'bitWidth').text)
    if element.find(spirit+'bitOffset') is not None:
        attrDict['bitOffset'] = int(element.find(spirit+'bitOffset').text)
    # check if bitWidth and bitOffset exist, if so create mask
    if 'bitWidth' in attrDict.keys() and 'bitOffset' in attrDict.keys():
        width = attrDict['bitWidth']
        offset = attrDict['bitOffset']
        attrDict['mask'] = format((2 ** width - 1) << offset, '#010x')
    # remove bitWidth and bitOffset
    attrDict.pop('bitWidth', None)
    attrDict.pop('bitOffset', None)

    if element.find(spirit+'access') is not None:
        attrDict['permission'] = permissionMap[element.find(
            spirit+'access').text]
    if element.find(spirit+'description') is not None:
        attrDict['description'] = element.find(
            spirit+'description').text.replace('\n', '').replace('\r', '')

    return attrDict


def main(inFile, outFile):
    msb = False
    lsb = False
    registerDict = {}
    fieldDict = {}

    # in file
    tree = etree.parse(inFile)
    root = tree.getroot()
    # out file
    outRoot = etree.Element('node')

    # depth first search
    queue = [root]

    while (len(queue) > 0):
        current = queue.pop(0)

        # find register
        if current.tag == spirit+'register':
            # check if register is msb or lsb
            found = current.find(spirit+'name')
            if 'MSB' in found.text:
                msb = True
            elif 'LSB' in found.text:
                lsb = True

            # the register only have 1 field and is not msb or lsb
            if len(current.findall(spirit+'field')) == 1 and not msb and not lsb:
                registerDict = elementParser(current)
                if 'id' in registerDict:
                    idTemp = registerDict['id']
                field = current.find(spirit+'field')
                registerDict = elementParser(field, registerDict)
                registerDict['id'] = idTemp

                register = etree.SubElement(outRoot, 'node', registerDict)

            # the register have multiple fields or is msb or lsb
            else:
                registerDict = elementParser(current)
                if (msb or lsb) and 'id' in registerDict:
                    registerDict['id'] = registerDict['id'][:-4]

                # check if both msb and lsb are true, it means currently it's lsb so add lsb to previous register
                if not msb or not lsb:
                    register = etree.SubElement(outRoot, 'node', registerDict)

                for field in current.findall(spirit+'field'):
                    if msb or lsb:
                        fieldDict = elementParser(field, registerDict)
                    else:
                        fieldDict = elementParser(field)

                    if msb and not lsb and 'id' in registerDict:
                        fieldDict['id'] = 'MSB'
                    elif lsb and 'id' in registerDict:
                        fieldDict['id'] = 'LSB'

                    etree.SubElement(register, 'node', fieldDict)

            if msb and lsb:
                msb = False
                lsb = False

        else:
            for child in current:
                queue.append(child)

    outTree = etree.ElementTree(outRoot)
    outTree.write(outFile, pretty_print=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='')
    parser.add_argument(
        "-ifs", help='xml input filename')
    parser.add_argument('-ofs', help='xml output filename')

    inFile = parser.parse_args().ifs
    outFile = parser.parse_args().ofs
    if inFile is None or not path.exists(inFile):
        print('invalid input filename')
        exit
    if outFile is None:
        print('invalid output filename')
        exit
    else:
        main(inFile, outFile)
