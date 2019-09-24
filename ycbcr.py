import time
import sys
import os
from collections import namedtuple
import numpy as np


class Y:
    """
    BASE
    """

    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.wh = self.width * self.height
        self.div = namedtuple('chroma_div', 'width height')

    def get_420_partitioning(self, width=None, height=None):
        if not width:
            wh = self.wh
        else:
            wh = width * height
        # start-stop
        #       y  y   cb  cb      cr      cr
        return (0, wh, wh, wh / 4 * 5, wh / 4 * 5, wh / 2 * 3)

    def get_422_partitioning(self, width=None, height=None):
        if not width:
            wh = self.wh
        else:
            wh = width * height
        # start-stop
        #       y  y   cb  cb      cr      cr
        return (0, wh, wh, wh / 2 * 3, wh / 2 * 3, wh * 2)


class Yuv(Y):
    def __init__(self, width, height):
        Y.__init__(self, width, height)

        # width, height
        self.chroma_div = self.div(2, 2)  # Chroma divisor w.r.t luma-size

    def get_frame_size(self, width=None, height=None):
        if not width:
            width = self.width
            height = self.height
        return (width * height * 3 / 2)

    def get_layout(self, width=None, height=None):
        """
        return a tuple of slice-objects
        Y|U|V
        """
        p = self.get_420_partitioning(width, height)
        return (slice(p[0], p[1]),  # start-stop for luma
                slice(p[2], p[3]),  # start-stop for chroma
                slice(p[4], p[5]))  # start-stop for chroma


class YCbCr:
    def __init__(
            self,
            width=0,
            height=0,
            filename=None,
            yuv_format_in=None,
            yuv_format_out=None,
            filename_diff=None,
            bitdepth=8, ):

        self.filename = filename
        self.filename_diff = filename_diff
        self.width = width
        self.height = height
        self.yuv_format_in = yuv_format_in
        self.yuv_format_out = yuv_format_out
        self.bitdepth = bitdepth
        self.yy = None
        self.cb = None
        self.cr = None

        self.yy_copy = None
        self.cb_copy = None
        self.cr_copy = None

        # Setup
        if self.yuv_format_in:  # we need a reader and and a writer just
            # to make sure
            self.reader = Yuv(self.width, self.height)
            self.writer = Yuv(self.width, self.height)
            self.frame_size_in = self.reader.get_frame_size()
            self.frame_size_out = self.reader.get_frame_size()

            # If file-sizes differ, just process the smaller ammount of frames
            bitsize = 1
            if self.bitdepth == 8:
                bitsize = 1
            else:
                bitsize = 2
            n1 = (os.path.getsize(self.filename[0]) / self.frame_size_in) / bitsize
            n2 = n1
            if self.filename_diff:
                n2 = (os.path.getsize(self.filename_diff[0]) / self.frame_size_in) / bitsize

            self.num_frames = min(n1, n2)
            self.layout_in = self.reader.get_layout()
            self.layout_out = self.reader.get_layout()
            self.frame_size_out = self.frame_size_in
            self.chroma_div = self.reader.chroma_div

        if self.yuv_format_out:
            self.writer = Yuv(self.width, self.height)
            self.frame_size_out = self.writer.get_frame_size()
            self.layout_out = self.writer.get_layout()

        # 8bpp -> 10bpp, 10->8 dito; special handling
        if yuv_format_in is not None:
            self.__check()

    def psnr(self, a, b):
        m = ((a - b) ** 2).mean()
        if m == 0:
            return float("nan")
        maxvalue = 255
        if self.bitdepth == 10:
            maxvalue = 1023
        return 10 * np.log10(maxvalue ** 2 / m)

    def psnr_all(self, out_file_id=0, in_file_id=0, psnr_contain=None):
        bd = []
        sum_yy = []
        sum_cb = []
        sum_cr = []
        if self.bitdepth == 8:
            read = self.__read_frame
        else:
            read = self.__read_frame_10
        with open(self.filename[in_file_id], 'rb') as fd_1, \
                open(self.filename_diff[out_file_id], 'rb') as fd_2:
            for i in xrange(self.num_frames):
                yy_frame, cb_frame, cr_frame = read(fd_1)
                crp_yy, crp_cb, crp_cr = read(fd_2)
                # frame2 = self.__copy_planes()[:-1]    # skip whole frame
                yy = self.psnr(yy_frame, crp_yy)
                cb = self.psnr(cb_frame, crp_cb)
                cr = self.psnr(cr_frame, crp_cr)
                bd.append((6 * yy + cb + cr) / 8.0)
                sum_yy.append(yy)
                sum_cb.append(cb)
                sum_cr.append(cr)
            psnr_contain[out_file_id * 4] = round(sum(bd) / len(bd), 2)
            psnr_contain[out_file_id * 4 + 1] = round(sum(sum_yy) / len(sum_yy), 2)
            psnr_contain[out_file_id * 4 + 2] = round(sum(sum_cb) / len(sum_cb), 2)
            psnr_contain[out_file_id * 4 + 3] = round(sum(sum_cr) / len(sum_cr), 2)

    def get_accout_diff(self):
        return len(self.filename_diff)

    def ssim(self):
        """
        http://en.wikipedia.org/wiki/Structural_similarity

        implementation using scipy and numpy from
        http://isit.u-clermont1.fr/~anvacava/code.html
        by antoine.vacavant@udamail.fr
        Usage by kind permission from author.
        """
        import scipy.ndimage
        from numpy.ma.core import exp
        from scipy.constants import pi

        def compute_ssim(img_mat_1, img_mat_2):
            # Variables for Gaussian kernel definition
            gaussian_kernel_sigma = 1.5
            gaussian_kernel_width = 11
            gaussian_kernel = np.zeros((gaussian_kernel_width, gaussian_kernel_width))

            # Fill Gaussian kernel
            for i in range(gaussian_kernel_width):
                for j in range(gaussian_kernel_width):
                    gaussian_kernel[i, j] = \
                        (1 / (2 * pi * (gaussian_kernel_sigma ** 2))) * \
                        exp(-(((i - 5) ** 2) + ((j - 5) ** 2)) / (2 * (gaussian_kernel_sigma ** 2)))

            # Convert image matrices to double precision (like in the Matlab version)
            img_mat_1 = img_mat_1.astype(np.float)
            img_mat_2 = img_mat_2.astype(np.float)

            # Squares of input matrices
            img_mat_1_sq = img_mat_1 ** 2
            img_mat_2_sq = img_mat_2 ** 2
            img_mat_12 = img_mat_1 * img_mat_2

            # Means obtained by Gaussian filtering of inputs
            img_mat_mu_1 = scipy.ndimage.filters.convolve(img_mat_1, gaussian_kernel)
            img_mat_mu_2 = scipy.ndimage.filters.convolve(img_mat_2, gaussian_kernel)

            # Squares of means
            img_mat_mu_1_sq = img_mat_mu_1 ** 2
            img_mat_mu_2_sq = img_mat_mu_2 ** 2
            img_mat_mu_12 = img_mat_mu_1 * img_mat_mu_2

            # Variances obtained by Gaussian filtering of inputs' squares
            img_mat_sigma_1_sq = scipy.ndimage.filters.convolve(img_mat_1_sq, gaussian_kernel)
            img_mat_sigma_2_sq = scipy.ndimage.filters.convolve(img_mat_2_sq, gaussian_kernel)

            # Covariance
            img_mat_sigma_12 = scipy.ndimage.filters.convolve(img_mat_12, gaussian_kernel)

            # Centered squares of variances
            img_mat_sigma_1_sq = img_mat_sigma_1_sq - img_mat_mu_1_sq
            img_mat_sigma_2_sq = img_mat_sigma_2_sq - img_mat_mu_2_sq
            img_mat_sigma_12 = img_mat_sigma_12 - img_mat_mu_12

            # c1/c2 constants
            # First use: manual fitting
            c_1 = 6.5025
            c_2 = 58.5225

            # Second use: change k1,k2 & c1,c2 depend on L (width of color map)
            l = 255
            k_1 = 0.01
            c_1 = (k_1 * l) ** 2
            k_2 = 0.03
            c_2 = (k_2 * l) ** 2

            # Numerator of SSIM
            num_ssim = (2 * img_mat_mu_12 + c_1) * (2 * img_mat_sigma_12 + c_2)
            # Denominator of SSIM
            den_ssim = (img_mat_mu_1_sq + img_mat_mu_2_sq + c_1) * \
                       (img_mat_sigma_1_sq + img_mat_sigma_2_sq + c_2)
            # SSIM
            ssim_map = num_ssim / den_ssim
            index = np.average(ssim_map)

            return index

        s = []
        with open(self.filename, 'rb') as fd_1, \
                open(self.filename_diff, 'rb') as fd_2:
            for i in xrange(self.num_frames):
                self.__read_frame(fd_1)
                data1 = self.yy.copy()
                self.__read_frame(fd_2)
                data2 = self.yy.copy()

                s.append(compute_ssim(np.reshape(data1, (self.height, self.width)),
                                      np.reshape(data2, (self.height, self.width))))

                yield s[-1]
            yield '--'
            yield sum(s) / len(s)

    def eight2ten(self):
        """
        8 bpp -> 10 bpp
        """
        a_in = np.memmap(self.filename, mode='readonly')
        a_out = np.memmap(self.filename_out, mode='write', shape=2 * len(a_in))
        a_out[::2] = a_in << 2
        a_out[1::2] = a_in >> 6

    def ten2eight(self):
        """
        10 bpp -> 8 bpp
        """
        fd_i = open(self.filename, 'rb')
        fd_o = open(self.filename_out, 'wb')

        while True:
            chunk = np.fromfile(fd_i, dtype=np.uint8, count=8192)
            chunk = chunk.astype(np.uint)
            if not chunk.any():
                break
            data = (2 + (chunk[1::2] << 8 | chunk[0::2])) >> 2

            data = data.astype(np.uint8, casting='same_kind')
            data.tofile(fd_o)

        fd_i.close()
        fd_o.close()

    def __check(self):
        """
        Basic consistency checks to prevent fumbly-fingers
        - width & height even multiples of 16
        - number of frames divides file-size evenly
        - for diff-cmd, file-sizes match
        """

        if self.width & 0xF != 0:
            print >> sys.stderr, "[WARNING] - width not divisable by 16"
        if self.height & 0xF != 0:
            print >> sys.stderr, "[WARNING] - hight not divisable by 16"

        size = os.path.getsize(self.filename[0])
        if not self.num_frames == size / float(self.frame_size_in):
            print >> sys.stderr, "[WARNING] - # frames not integer"

        if self.filename_diff:
            size_diff = os.path.getsize(self.filename_diff[0])
            if not size == size_diff:
                print >> sys.stderr, "[WARNING] - file-sizes are not equal"

    def __read_frame(self, fd):
        """
        Use extended indexing to read 1 frame into self.{y, cb, cr}
        """
        self.raw = np.fromfile(fd, dtype=np.uint8, count=self.frame_size_in)
        self.raw = self.raw.astype(np.int, copy=False)
        yy = self.raw[self.layout_in[0]]
        cb = self.raw[self.layout_in[1]]
        cr = self.raw[self.layout_in[2]]
        return yy, cb, cr

    def __read_frame_10(self, fd, tag):
        """
        Use extended indexing to read 1 frame into self.{y, cb, cr}
        """
        self.raw = np.fromfile(fd, dtype=np.uint16, count=self.frame_size_in)
        self.raw = self.raw.astype(np.uint16)
        if tag is 0:
            self.yy = self.raw[self.layout_in[0]]
            self.cb = self.raw[self.layout_in[1]]
            self.cr = self.raw[self.layout_in[2]]
        else:
            self.yy_copy = self.raw[self.layout_in[0]]
            self.cb_copy = self.raw[self.layout_in[1]]
            self.cr_copy = self.raw[self.layout_in[2]]

    def __write_frame(self, fd):
        """
        Use extended indexing to write 1 frame, including re-sampling and
        format conversion
        """
        self.__resample()
        data = np.empty(self.frame_size_out, dtype=np.uint8)

        data[self.layout_out[0]] = self.yy
        data[self.layout_out[1]] = self.cb
        data[self.layout_out[2]] = self.cr

        data.tofile(fd)

    def __crop(self, arg):
        """
        Crop color-planes
        Layout for 4:2:0
        X - Luma sample
        O - Co-located chroma sample
            i.e. 1 chroma for 4 Luma

        X     X     X     X
           O           O
        X     X     X     X
        X     X     X     X
           O           O
        X     X     X     X

        Layout for 4:2:2

        X     X     X     X
        O           O
        X     X     X     X
        O           O
        X     X     X     X
        O           O
        X     X     X     X
        O           O
        """
        d = self.chroma_div  # divisor
        r = self.crop_rect

        self.yy = np.reshape(self.yy, (self.height, self.width))
        self.yy = self.yy[r.ys:r.ye + 1, r.xs:r.xe + 1]

        self.yy = self.yy.reshape(-1)

        self.cb = self.cb.reshape([self.height / d.height,
                                   self.width / d.width])
        self.cb = self.cb[r.ys / d.height:
                          r.ye / d.height + 1,
                  r.xs / d.width:
                  r.xe / d.width + 1]
        self.cb = self.cb.reshape(-1)

        self.cr = self.cr.reshape([self.height / d.height,
                                   self.width / d.width])
        self.cr = self.cr[r.ys / d.height:
                          r.ye / d.height + 1,
                  r.xs / d.width:
                  r.xe / d.width + 1]
        self.cr = self.cr.reshape(-1)
