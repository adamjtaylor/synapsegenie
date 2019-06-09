import pytest
import mock
import synapseclient
from synapseclient.exceptions import SynapseHTTPError
from genie import validate
import pandas as pd
center = "SAGE"
syn = mock.create_autospec(synapseclient.Synapse)


@pytest.fixture(params=[
    # tuple with (input, expectedOutput)
    (["data_CNA_SAGE.txt"], "cna"),
    (["data_clinical_supp_SAGE.txt"], "clinical"),
    (["data_clinical_supp_sample_SAGE.txt",
      "data_clinical_supp_patient_SAGE.txt"], "clinical")])
def filename_fileformat_map(request):
    return request.param


def test_perfect_determine_filetype(filename_fileformat_map):
    '''
    Tests determining of file type through filenames
    Parameters are passed in from filename_fileformat_map
    '''
    (filepath_list, fileformat) = filename_fileformat_map
    assert validate.determine_filetype(
        syn, filepath_list, center) == fileformat


def test_wrongfilename_noerror_determine_filetype():
    '''
    Tests None is passed back when wrong filename is passed
    when raise_error flag is False
    '''
    filetype = validate.determine_filetype(
        syn, ['wrong.txt'], center)
    assert filetype is None


def test_valid_determine_validity_and_log():
    '''
    Tests if no error and warning strings are passed that
    returned valid and message is correct
    '''
    valid, message = \
        validate.determine_validity_and_log('', '')
    assert valid
    assert message == "YOUR FILE IS VALIDATED!\n"


def test_invalid_determine_validity_and_log():
    '''
    Tests if error and warnings strings are passed that
    returned valid and message is correct
    '''
    valid, message = \
        validate.determine_validity_and_log("error\nnow", 'warning\nnow')
    assert not valid
    assert message == (
        "----------------ERRORS----------------\n"
        "error\nnow"
        "-------------WARNINGS-------------\n"
        'warning\nnow')


def test_warning_determine_validity_and_log():
    '''
    Tests if no error but warnings strings are passed that
    returned valid and message is correct
    '''
    valid, message = \
        validate.determine_validity_and_log('', 'warning\nnow')
    assert valid
    assert message == (
        "YOUR FILE IS VALIDATED!\n"
        "-------------WARNINGS-------------\n"
        'warning\nnow')


def test_valid_validate_single_file():
    '''
    Tests that all the functions are run in validate single
    file workflow and all the right things are returned
    '''
    filepathlist = ['clinical.txt']
    error_string = ''
    warning_string = ''
    center = 'SAGE'
    expected_valid = True
    expected_message = "valid message here!"
    expected_filetype = "clinical"
    with mock.patch(
            "genie.validate.determine_filetype",
            return_value=expected_filetype) as mock_determine_filetype,\
        mock.patch(
            "genie.clinical.validate",
            return_value=(error_string, warning_string)) as mock_genie_class,\
        mock.patch(
            "genie.validate.determine_validity_and_log",
            return_value=(expected_valid, expected_message)) as mock_determine:

        valid, message, filetype = validate.validate_single_file(
            syn,
            filepathlist,
            center)

        assert valid == expected_valid
        assert message == expected_message
        assert filetype == expected_filetype

        mock_determine_filetype.assert_called_once_with(
            syn, filepathlist, center)

        mock_genie_class.assert_called_once_with(
            filePathList=filepathlist,
            oncotreeLink=None,
            testing=False,
            noSymbolCheck=False)

        mock_determine.assert_called_once_with(error_string, warning_string)


def test_filetype_validate_single_file():
    '''
    Tests that if filetype is passed in that an error is thrown
    if it is an incorrect filetype
    '''
    filepathlist = ['clinical.txt']
    center = "SAGE"
    with pytest.raises(
            ValueError,
            match="Your filename is incorrect! "
                  "Please change your filename before you run "
                  "the validator or specify --filetype if you are "
                  "running the validator locally"):
        validate.validate_single_file(
            syn,
            filepathlist,
            center,
            filetype="foobar")


def test_wrongfiletype_validate_single_file():
    '''
    Tests that if there is no filetype for the filename passed
    in, an error is thrown
    '''
    filepathlist = ['clinical.txt']
    center = "SAGE"
    with mock.patch(
            "genie.validate.determine_filetype",
            return_value=None) as mock_determine_filetype,\
        pytest.raises(
            ValueError,
            match="Your filename is incorrect! "
                  "Please change your filename before you run "
                  "the validator or specify --filetype if you are "
                  "running the validator locally"):
        validate.validate_single_file(
            syn,
            filepathlist,
            center)
        mock_determine_filetype.assert_called_once_with(
            syn, filepathlist, center)


def test_invalid__check_parentid_input():
    '''
    Test that parentid or filetype cant be specified together
    '''
    with pytest.raises(
            ValueError,
            match="If you used --parentid, you must not use --filetype"):
        validate._check_parentid_input("foo", "foo")


def test_valid__check_parentid_input():
    '''
    Test that parentid or filetype can be specified without error
    '''
    validate._check_parentid_input(None, "foo")
    validate._check_parentid_input(None, None)
    validate._check_parentid_input("foo", None)


def test_nopermission__check_parentid_permission_container():
    '''
    Error thrown if no permissions to access
    '''
    parentid = "syn123"
    with mock.patch.object(syn, "get", side_effect=SynapseHTTPError),\
        pytest.raises(
            ValueError,
            match="Provided Synapse id must be your input folder Synapse id "
                  "or a Synapse Id of a folder inside your input directory"):
        validate._check_parentid_permission_container(syn, parentid)


def test_notcontainer__check_parentid_permission_container():
    '''
    If input if synid of file, throw error
    '''
    parentid = "syn123"
    file_ent = synapseclient.File("foo", parentId=parentid)
    with mock.patch.object(syn, "get", return_value=file_ent),\
        pytest.raises(
            ValueError,
            match="Provided Synapse id must be your input folder Synapse id "
                  "or a Synapse Id of a folder inside your input directory"):
        validate._check_parentid_permission_container(syn, parentid)


def test_valid__check_parentid_permission_container():
    '''
    Test that parentid specified is a container and have permissions to access
    '''
    parentid = "syn123"
    folder_ent = synapseclient.Folder("foo", parentId=parentid)
    with mock.patch.object(syn, "get", return_value=folder_ent):
        validate._check_parentid_permission_container(syn, parentid)


def test_valid__check_center_input():
    center = "FOO"
    center_list = ["FOO", "WOW"]
    validate._check_center_input(center, center_list)


def test_invalid__check_center_input():
    center = "BARFOO"
    center_list = ["FOO", "WOW"]
    with pytest.raises(
            ValueError,
            match="Must specify one of these centers: {}".format(
                  ", ".join(center_list))):
        validate._check_center_input(center, center_list)


class argparser:
    oncotreelink = "link"
    parentid = None
    filetype = None
    testing = False
    center = "try"
    filepath = "path.csv"
    nosymbol_check = False

    def asDataFrame(self):
        database_dict = {"Database": ["centerMapping"],
                         "Id": ["syn123"],
                         "center": ["try"]}
        databasetosynid_mappingdf = pd.DataFrame(database_dict)
        return(databasetosynid_mappingdf)


def test_perform_validate():
    arg = argparser()
    check_input_call = "genie.validate._check_parentid_input"
    check_perm_call = "genie.validate._check_parentid_permission_container"
    check_center_call = "genie.validate._check_center_input"
    validate_file_call = "genie.validate.validate_single_file"
    with mock.patch(check_input_call) as patch_check_input,\
        mock.patch(check_perm_call) as patch_check_parentid,\
        mock.patch.object(
            syn,
            "tableQuery",
            return_value=arg) as patch_syn_tablequery,\
        mock.patch(check_center_call) as patch_check_center,\
        mock.patch(
            validate_file_call,
            return_value=('foo', 'foo', 'foo')) as patch_validate:
        validate.perform_validate(syn, arg)
        # Check values function call and values here
