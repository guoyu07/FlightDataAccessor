

#-------------------------------------------------------------------------------
# Parameter container Class
# =========================
class Parameter(object):
    def __init__(self, name, array=[], frequency=1, offset=0):
        '''
        :param name: Parameter name
        :type name: String
        :param array: Masked array of data for the parameter.
        :type array: np.ma.masked_array
        :param frequency: Sample Rate / Frequency / Hz
        :type frequency: Int
        :param offset: Offset in Frame.
        :type offset: Float
        '''
        self.name = name
        self.array = array
        self.frequency = self.sample_rate = self.hz = frequency
        self.offset = offset
        
    def __repr__(self):
        return "%s %sHz %.2fsecs" % (self.name, self.frequency, self.offset)

P = Parameter # shorthand