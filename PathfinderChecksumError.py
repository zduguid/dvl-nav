class PathfinderChecksumError(Exception):
    """Raised when an invalid checksum is found
    """
    def __init__(self, calc_checksum, given_checksum):
        self.calc_checksum  = calc_checksum
        self.given_checksum = given_checksum

    def __str__(self):
        return('Calculated %d, Given: %d' % 
          (self.calc_checksum, self.given_checksum))