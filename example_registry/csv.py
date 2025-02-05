import logging
import os

import synapseclient

from synapsegenie.example_filetype_format import FileTypeFormat
from synapsegenie import process_functions

logger = logging.getLogger(__name__)


class Csv(FileTypeFormat):

    _filetype = "csv"

    _process_kwargs = ["newPath", "databaseSynId"]

    def _validate_filetype(self, filePath):
        assert os.path.basename(filePath).endswith(".csv")

    def _process(self, df):
        df.columns = [col.upper() for col in df.columns]
        return df

    def process_steps(self, df, newPath, databaseSynId):
        df = self._process(df)
        # TODO: no center column in Synapse table
        # process_functions.update_data(
        #     syn=self.syn, databaseSynId=databaseSynId, newData=df,
        #     filterBy=self.center, toDelete=True
        # )
        df.to_csv(newPath, sep="\t", index=False)
        return newPath

    def _validate(self, df):
        total_error = ""
        warning = ""
        if df.empty:
            total_error += "{}: File must not be empty".format(self._filetype)
        return total_error, warning
