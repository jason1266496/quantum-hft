"""Original numerical/comparison logic plus explicit stage-schema checks."""
from experiments.phase4a4.analysis import none_config,only_weight_changed,kernel_check,majority,changes
from experiments.phase4a4.analysis import compare_repeats as original_compare
from .schema import validate_stage
def compare_repeats(first,repeat,*,true_labels=None):
    validate_stage(first,true_labels);validate_stage(repeat,true_labels)
    return original_compare(first,repeat)
