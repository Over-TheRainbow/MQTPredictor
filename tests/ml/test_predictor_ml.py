from pathlib import Path
from unittest.mock import patch

import pytest
from mqt.bench import benchmark_generator

from mqt.predictor import ml


@patch("matplotlib.pyplot.show")
def test_predict(mock_show):
    path = ml.helper.get_path_trained_model() / "trained_clf.joblib"
    assert path.is_file()
    filename = "test_qasm.qasm"
    qc = benchmark_generator.get_benchmark("dj", 1, 8)
    qc.qasm(filename=filename)
    predictor = ml.Predictor()
    prediction = predictor.predict(filename)
    assert prediction >= 0 and prediction < len(ml.helper.get_index_to_comppath_LUT())
    prediction = predictor.predict(qc.qasm())
    assert prediction >= 0 and prediction < len(ml.helper.get_index_to_comppath_LUT())
    prediction = predictor.predict("fail test")
    assert not prediction

    predictor.clf = None
    prediction = predictor.predict(filename)
    Path(filename).unlink()
    assert prediction >= 0 and prediction < len(ml.helper.get_index_to_comppath_LUT())


@pytest.mark.parametrize(
    "comp_path", list(range(len(ml.helper.get_index_to_comppath_LUT())))
)
def test_compilation_paths(comp_path):
    predictor = ml.Predictor()
    qc_qasm = benchmark_generator.get_benchmark("dj", 1, 2).qasm()
    res, device = predictor.compile_predicted_compilation_path(qc_qasm, comp_path)
    assert res and device
    qc = benchmark_generator.get_benchmark("dj", 1, 2)
    tmp_filename = "test.qasm"
    qc.qasm(filename=tmp_filename)
    res, device = predictor.compile_predicted_compilation_path(tmp_filename, comp_path)
    assert res and device
    if Path(tmp_filename).exists():
        Path(tmp_filename).unlink()


def test_compile_all_circuits_for_qc():
    qc = benchmark_generator.get_benchmark("dj", 1, 2)
    tmp_filename = "test.qasm"
    qc.qasm(filename=tmp_filename)
    predictor = ml.Predictor()
    assert predictor.compile_all_circuits_for_qc(
        filename=tmp_filename,
        source_path=".",
    )
    if Path(tmp_filename).exists():
        Path(tmp_filename).unlink()


@patch("matplotlib.pyplot.show")
def test_train_random_forest_classifier(mock_pyplot):
    predictor = ml.Predictor()
    assert predictor.clf is None
    predictor.train_random_forest_classifier(visualize_results=False)
    if Path("non_zero_indices.npy").exists():
        Path("non_zero_indices.npy").unlink()

    assert predictor.clf is not None


def test_generate_compiled_circuits():

    predictor = ml.Predictor()
    source_path = "."
    target_path = Path("test_compiled_circuits")
    if not target_path.exists():
        target_path.mkdir()

    qc = benchmark_generator.get_benchmark("dj", 1, 3)
    qasm_path = Path("compiled_test.qasm")
    qc.qasm(filename=str(qasm_path))
    predictor.generate_compiled_circuits(source_path, str(target_path))

    training_sample, circuit_name, scores = predictor.generate_training_sample(
        str(qasm_path), source_path, target_path
    )
    assert training_sample
    assert circuit_name
    assert scores

    (
        training_data,
        name_list,
        scores_list,
    ) = predictor.generate_trainingdata_from_qasm_files(source_path, str(target_path))
    assert training_data
    assert name_list
    assert scores_list

    if target_path.exists():
        for file in target_path.iterdir():
            file.unlink()
        target_path.rmdir()

    if qasm_path.exists():
        qasm_path.unlink()
