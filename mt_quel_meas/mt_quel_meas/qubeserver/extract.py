
import numpy as np
from mt_util.tunits_util import FrequencyType
from mt_quel_meas.job import MeasurementDataset, Job, TranslationInfo
from mt_quel_meas.qubeserver.job import JobQubeServer

def extract_dataset(job: Job, job_qube_server: JobQubeServer, translate: TranslationInfo, dataset: dict) -> MeasurementDataset:
    # TODO
    translate_dataset = MeasurementDataset(shape = [], dataarray = [])
    return translate_dataset


