import torch.nn.functional as F
from torch.autograd import Function
import torch


class PeakStimulation(Function):

    @staticmethod
    def forward(ctx, input, return_aggregation, win_size, peak_filter):
        ctx.num_flags = 4

        # assert win_size % 2 == 1, 'Window size for peak finding must be odd.'
        # offset = (win_size - 1) // 2
        # padding = torch.nn.ConstantPad2d(offset, float('-inf'))
        # padded_maps = padding(input)
        # batch_size, num_channels, h, w = padded_maps.size()
        # element_map = torch.arange(0, h * w).long().view(1, 1, h, w)[:, :, offset: -offset, offset: -offset]
        # element_map = element_map.to(input.device)
        # _, indices = F.max_pool2d(
        #     padded_maps,
        #     kernel_size=win_size,
        #     stride=1,
        #     return_indices=True)
        # peak_map = (indices == element_map)

        peak_map = None
        if type(win_size) == type([1, 2, 3]):
            for win in win_size:
                offset = (win - 1) // 2
                padding = torch.nn.ConstantPad2d(offset, float('-inf'))
                padded_maps = padding(input)
                batch_size, num_channels, h, w = padded_maps.size()
                element_map = torch.arange(0, h * w).long().view(1, 1, h, w)[:, :, offset: -offset, offset: -offset]
                element_map = element_map.to(input.device)
                _, indices = F.max_pool2d(
                    padded_maps,
                    kernel_size=win,
                    stride=1,
                    return_indices=True)
                if peak_map is None:
                    peak_map = (indices == element_map)
                else:
                    peak_map += peak_map

        else:
            offset = (win_size - 1) // 2
            padding = torch.nn.ConstantPad2d(offset, float('-inf'))
            padded_maps = padding(input)
            batch_size, num_channels, h, w = padded_maps.size()
            element_map = torch.arange(0, h * w).long().view(1, 1, h, w)[:, :, offset: -offset, offset: -offset]
            element_map = element_map.to(input.device)
            _, indices = F.max_pool2d(
                padded_maps,
                kernel_size=win_size,
                stride=1,
                return_indices=True)
            peak_map = (indices == element_map)
            np_input_person = padded_maps.cpu().data.numpy()[0, 16, :, :]
            person_indices = indices.cpu().data.numpy()[0, 16, :, :]
            np_peak_map_person = peak_map.cpu().data.numpy()[0, 16, :, :]

        # peak filtering
        if peak_filter:
            mask = input >= peak_filter(input)
            peak_map = (peak_map * mask)
        peak_list = torch.nonzero(peak_map)
        ctx.mark_non_differentiable(peak_list)

        # peak aggregation
        if return_aggregation:
            peak_map = peak_map.float()
            ctx.save_for_backward(input, peak_map)
            return peak_list, (input * peak_map).view(batch_size, num_channels, -1).sum(2) / peak_map.view(batch_size,
                                                                                                           num_channels,
                                                                                                           -1).sum(2)
        else:
            return peak_list

    @staticmethod
    def backward(ctx, *grad_outputs):
        input, peak_map, = ctx.saved_tensors
        batch_size, num_channels, _, _ = input.size()
        grad_input = peak_map * grad_outputs[-1].view(batch_size, num_channels, 1, 1)

        return (grad_input,) + (None,) * ctx.num_flags


def peak_stimulation(input, return_aggregation=True, win_size=[3, 5, 7], peak_filter=None):
    return PeakStimulation.apply(input, return_aggregation, win_size, peak_filter)
