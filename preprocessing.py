import os
import blockMetaData as md


def addBlockHeightToFileName(fileLocation, fileName, height):
    if len(height) < 6:
        height = '0'*(6-len(height))+height
    os.rename(fileLocation+r'/'+fileName, fileLocation+ r'/' + height +'_' +fileName)


def addBlockHeightForDirectory(directory):
    relevant_path_endings = ['.mempool', '.block', '.gbt']
    blockHeights = {}
    for file in os.listdir(directory):
        if file.find("_") == -1 and any(x in file for x in relevant_path_endings):
            print("trying file: " + file)
            blockId = file[0:file.find(r'.')]
            height = -1
            if blockId in blockHeights:
                height = int(blockHeights[blockId])
            else:
                blockData = md.getBlockInfo(blockId)
                if (blockData != None):
                    height = int(blockData['height'])
                    blockHeights[blockId] = height
                elif (blockData == None):
                    os.rename(file, 'X_' + file + '_not_found')
                    print("height for " + blockId + " not found")
                    continue
            if height < 0:
                raise Exception("height for " + blockId + " not found")
            addBlockHeightToFileName(directory, file, str(height))


def createAllowListFile(directory, resultFile):
    print("start allowset")
    txSet = set()
    for file in os.listdir(directory):
        if file.endswith('.block'):
            print("looking at: "+file)
            with open(os.path.join(directory,file), 'r') as import_file:
                if file.find('_')!=-1:
                    height = file[0:6]
                else:
                    height = 'height not found'
                for line in import_file:
                    # Skip header line in block file
                    if 'fees' in line:
                        continue
                    line = line.rstrip('\n')#+' '+height
                    txSet.add(line)
            import_file.close()
    resFile = open(os.path.join(directory, resultFile+".allow"),'a')
    for tx in txSet:
        resFile.write(tx+'\n')
    resFile.close()
    return txSet


def createCoinbaseWeightsDict(directory, resultFile):
    coinbaseWeights = {}
    coinbase_file_name = os.path.join(directory, resultFile+'.coinbases')
    if (os.path.exists(coinbase_file_name) and os.path.getsize(coinbase_file_name) > 0):
        with open(coinbase_file_name, 'r') as coinbase_weight_file:
             for line in coinbase_weight_file:
                lineItems = line.rstrip('\n').split(' ')
                coinbaseWeights[int(lineItems[0])] = int(lineItems[1].rstrip('\n'))
        coinbase_weight_file.close()

    coinbase_weight_file = open(os.path.join(directory, resultFile+".coinbases"),'a')
    for file in os.listdir(directory):
        if file.endswith('.block'):
            print("Looking for coinbase weight for " + file)
            height = int(file[0:file.find('_')])
            if height in coinbaseWeights:
                print('height ' + str(height) + ' found, skipping…')
                continue
            else:
                with open(os.path.join(directory, file), 'r') as import_file:
                    import_file.readline()
                    coinbaseTxId = import_file.readline().rstrip('\n')
                    coinbaseWeights[height] = md.getTxWeight(coinbaseTxId)
                    print('Could not find entry, looking up height ' + str(height) + ' txid ' + coinbaseTxId)
                    coinbase_weight_file.write(str(height) + ' ' + str(coinbaseWeights[height]) + '\n')
    coinbase_weight_file.close()


def create_diff_pools(directory):
    allowed_txids = set()
    for file in os.listdir(directory):
        if file.endswith('.allow'):
            with open(os.path.join(directory, file), 'r') as allow_file:
                for line in allow_file:
                    allowed_txids.add(line.strip('\n'))

    seen_txids = set()
    for file in sorted(os.listdir(directory)):
        if file.endswith('.mempool'):
            if '_' not in file:
                raise Exception("mempool " + file + " has no height")
            print('Making .diffpool for ' + file)
            with open(os.path.join(directory, file), 'r') as mempool_file:
                stub = file.split('.')[0]
                with open(os.path.join(directory, stub + '.diffpool'), 'w') as diffpool_file:
                    for line in mempool_file:
                        if '#' in line:
                            # copy file header
                            diffpool_file.write(line)
                            continue
                        line_items = line.rstrip('\n').split(' ')
                        txid = line_items[0]
                        if txid not in seen_txids and txid in allowed_txids:
                            seen_txids.add(txid)
                            diffpool_file.write(line)

if __name__ == '__main__':
    directory = '.'
    addBlockHeightForDirectory(directory)
    createAllowListFile(directory, 'txset')
    createCoinbaseWeightsDict(directory, 'weight')
    #print("dict "+str(getCoinbaseSizes(directory)))
    create_diff_pools(directory)
