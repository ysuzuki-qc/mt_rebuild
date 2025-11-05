
import numpy as np
from mt_util.tunits_util import FrequencyType
from mt_quel_meas.job import MeasurementDataset, Job, TranslationInfo
from mt_quel_meas.labrad.labrad_job import JobLabrad

def extract_job_result(job: Job, job_labrad: JobLabrad, translate: TranslationInfo, dataset: dict) -> MeasurementDataset:
    # TODO
    translate_dataset = MeasurementDataset(shape = [], dataarray = [])
    return translate_dataset


