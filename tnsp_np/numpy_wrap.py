from numpy import *


from builtins import bool, int, float, complex, object, str
unicode = str
from numpy import round, abs, max, min


class tensor(ndarray):
    def __new__(cls, input_array, legs=None):
        obj = asarray(input_array).view(cls)
        return obj

    def __init__(self, input_array, legs=None):
        self.legs = [str(legs[i]) for i in range(self.ndim)]
        assert len(set(self.legs)) == len(self.legs), "repeated legs name"

    def __repr__(self):
        return f'{super(tensor, self).__repr__()}\nlegs({self.legs})'

    def __reduce__(self):
        pickled_state = super(tensor, self).__reduce__()
        new_state = pickled_state[2] + (self.legs,)
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state):
        self.legs = state[-1]
        super(tensor, self).__setstate__(state[0:-1])

    def __array_finalize__(self, obj):
        if obj is None:
            return
        legs = getattr(obj, 'legs', None)
        self.legs = legs
        return

    def __getitem__(self, args):
        res = super(tensor, self).__getitem__(args)
        if not isinstance(res, ndarray):
            return res
        if not isinstance(args, tuple):
            args = (args,)
        legs_to_del = [i for i, j in enumerate(args) if isinstance(j, int)]
        tmp_legs = [j for i, j in enumerate(self.legs) if i not in legs_to_del]
        res.set_legs(tmp_legs)
        return res

    def __add__(self, args):
        if isinstance(args, type(self)):
            return super(tensor, self).__add__(args.tensor_transpose(self.legs))
        else:
            return super(tensor, self).__add__(args)

    def __iadd__(self, args):
        if isinstance(args, type(self)):
            return super(tensor, self).__iadd__(args.tensor_transpose(self.legs))
        else:
            return super(tensor, self).__iadd__(args)

    def __sub__(self, args):
        if isinstance(args, type(self)):
            return super(tensor, self).__sub__(args.tensor_transpose(self.legs))
        else:
            return super(tensor, self).__sub__(args)

    def __isub__(self, args):
        if isinstance(args, type(self)):
            return super(tensor, self).__isub__(args.tensor_transpose(self.legs))
        else:
            return super(tensor, self).__isub__(args)

    def __mul__(self, args):
        if isinstance(args, type(self)):
            if self.ndim == 0:
                return args.__mul__(self)
            else:
                return super(tensor, self).__mul__(args)
        else:
            return super(tensor, self).__mul__(args)

    def set_legs(self, legs):
        self.legs = [str(legs[i]) for i in range(self.ndim)]
        assert len(set(self.legs)) == len(self.legs), "repeated legs name"
        return self

    def rename_legs(self, legs_dict, restrict_mode=True):
        for i, j in legs_dict.items():
            if str(i) in self.legs:
                self.legs[self.legs.index(str(i))] = str(j)
            else:
                if restrict_mode:
                    raise Exception("leg not found")
        assert len(set(self.legs)) == len(self.legs), "repeated legs name"
        return self

    def tensor_transpose(self, legs):
        res = self.transpose([self.legs.index(str(i)) for i in legs])
        res.set_legs(legs)
        return res

    def tensor_contract(self, tensor, legs1, legs2,
                        legs_dict1=None, legs_dict2=None, restrict_mode=True):
        tensor1 = self
        tensor2 = tensor
        legs_dict1 = {} if legs_dict1 is None else legs_dict1
        legs_dict2 = {} if legs_dict2 is None else legs_dict2
        order1 = []
        order2 = []
        correct_legs1 = []
        correct_legs2 = []
        for i, j in zip(legs1, legs2):
            if i in tensor1.legs and j in tensor2.legs:
                order1.append(tensor1.legs.index(str(i)))
                order2.append(tensor2.legs.index(str(j)))
                correct_legs1.append(str(i))
                correct_legs2.append(str(j))
            else:
                if restrict_mode:
                    raise Exception("leg not match contract")
        legs = [j if j not in legs_dict1 else legs_dict1[j]
                for j in tensor1.legs if j not in correct_legs1] +\
            [j if j not in legs_dict2 else legs_dict2[j]
             for j in tensor2.legs if j not in correct_legs2]
        res = tensordot(tensor1, tensor2, [order1, order2])
        return self.__class__(res, legs=legs)

    def tensor_multiple(self, arr, leg, restrict_mode=True):
        if leg not in self.legs:
            if restrict_mode:
                raise Exception("leg not match in multiple")
        else:
            shape = ones(self.ndim, dtype=int)
            shape[self.legs.index(leg)] = -1
            self *= asarray(arr).reshape(shape)
        return self

    """
    def __matmul__(self, b):
        res = super().dot(b)
        if self.ndim is not 2 or b.ndim is not 2:
            raise Exception("ambiguous dot")
        res.rename_legs({self.legs[1]:b.legs[1]})
        return res
    """

    """
    def inverse(self):
        res = linalg.inv(self)
        pass
    """

    def tensor_svd(self, legs1, legs2, new_legs, restrict_mode=True, *args, **kw):
        assert set(legs1) | set(legs2) >= set(self.legs) or set(legs1) & set(legs2) == set(), "svd legs not correct"
        if restrict_mode:
            assert set(legs1) | set(legs2) == set(self.legs), "svd legs not correct"
        legs1 = [i for i in self.legs if i in legs1]
        legs2 = [i for i in self.legs if i in legs2]
        transposed = self.tensor_transpose([*legs1, *legs2])
        size1 = prod(transposed.shape[:len(legs1)], dtype=int)
        size2 = prod(transposed.shape[len(legs1):], dtype=int)
        tensor1, env, tensor2 = linalg.svd(transposed.reshape(
            [size1, size2]), *args, **kw)
        assert tensor1.shape[:-1] == size1
        assert tensor2.shape[1:] == size2
        tensor1 = tensor1.reshape([*transposed.shape[:len(legs1)], tensor1.size//size1])
        tensor2 = tensor2.reshape([tensor2.size//size2, *transposed.shape[len(legs1):]])
        if not isinstance(new_legs, list):
            new_legs = [new_legs, new_legs]
        tensor1.set_legs([*legs1, new_legs[0]])
        tensor2.set_legs([new_legs[1], *legs2])
        return tensor1, env, tensor2

    """
    def tensor_svd_cut():
        pass
    """

    def tensor_qr(self, legs1, legs2, new_legs, restrict_mode=True, *args, **kw):
        assert set(legs1) | set(legs2) >= set(self.legs) or set(legs1) & set(legs2) == set(), "qr legs not correct"
        if restrict_mode:
            assert set(legs1) | set(legs2) == set(self.legs), "qr legs not correct"
        legs1 = [i for i in self.legs if i in legs1]
        legs2 = [i for i in self.legs if i in legs2]
        transposed = self.tensor_transpose([*legs1, *legs2])
        size1 = prod(transposed.shape[:len(legs1)], dtype=int)
        size2 = prod(transposed.shape[len(legs1):], dtype=int)
        tensor1, tensor2 = linalg.qr(transposed.reshape(
            [size1, size2]), *args, **kw)
        assert tensor1.shape[:-1] == size1
        assert tensor2.shape[1:] == size2
        tensor1 = tensor1.reshape([*transposed.shape[:len(legs1)], tensor1.size//size1])
        tensor2 = tensor2.reshape([tensor2.size//size2, *transposed.shape[len(legs1):]])
        if not isinstance(new_legs, list):
            new_legs = [new_legs, new_legs]
        tensor1.set_legs([*legs1, new_legs[0]])
        tensor2.set_legs([new_legs[1], *legs2])
        return tensor1, tensor2


tensor_transpose = tensor.tensor_transpose
tensor_contract = tensor.tensor_contract
tensor_svd = tensor.tensor_svd
tensor_qr = tensor.tensor_qr
