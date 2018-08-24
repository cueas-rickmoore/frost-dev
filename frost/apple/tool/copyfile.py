
import datetime
import numpy as N

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def exclude(path, exclusions):
    if exclusions is None: return False
    elif isinstance(exclusions, basestring):
        return path == exclusions 
    else: return path in exclusions

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def sanitizeDataset(builder, path, debug):
    builder.open('r')
    # make sure the dataset is not corrupted with bogus values
    last_valid = builder.dateAttribute(path, 'last_valid_date', None)
    if last_valid is not None:
        end_date = builder.dateAttribute(path, 'end_date')
        first_invalid = last_valid + datetime.timedelta(days=1)
        if debug: \
           print path, 'last valid', last_valid, 'first invalid', first_invalid
        if first_invalid <= end_date:
            data = builder.dataSince(path, first_invalid)
            missing = builder.datasetAttribute(path, 'missing', None)
            if missing is None:
                if data.dtype == N.int16: missing = -32768
                elif data.dtype == N.bool: missing = False
                else:
                    print path, data.dtype
                    exit()
            builder.close()
            data[:,:,:] = missing
            builder.open('a')
            builder.insertByDate(path, data, first_invalid)
    builder.close()

# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - 

def copyHdf5DategridFile(reader, builder, fileattrs, datasets, exclusions=None,
                         debug=False):
    builder.open('a')
    builder.setFileAttributes(**dict(reader.getFileAttributes()))
    builder.setFileAttributes(**dict(fileattrs))
    builder.close()

    for path in reader.group_names:
        if not exclude(path, exclusions):
            attrs = reader.getGroupAttributes(path)
            if debug: print "creating '%s' group" % path
            builder.open('a')
            builder.createGroup(path)
            builder.setGroupAttributes(path, **attrs)
            builder.close()

    for path in reader.dataset_names:
        if not exclude(path, exclusions):
            if debug: print "creating '%s' dataset" % path
            dataset = reader.getDataset(path)
            builder.open('a')
            if dataset.chunks is not None:
                builder.createDataset(path, dataset, chunks=dataset.chunks,
                                      compression='gzip')
            else: builder.createDataset(path, dataset)
            builder.close()
            builder.open('a')
            builder.setDatasetAttributes(path, **dict(dataset.attrs))
            builder.close()
            if path in datasets:
                builder.open('a')
                builder.setDatasetAttributes(path, **datasets[path])
                builder.close()
            if not ('provenance' in path):
                if debug: print '    calling dataset sanitizer'
                sanitizeDataset(builder, path, debug)

    reader.close()
    builder.close()

