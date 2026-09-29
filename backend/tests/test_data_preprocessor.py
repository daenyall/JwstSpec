from DataPreprocess import DataPreprocessor


def test_classify_bin_quality_valid():
    preprocessor = DataPreprocessor()

    status, reasons = preprocessor._classify_bin_quality(
        median_flux=1.0,
        median_snr=100.0,
        negative_fraction=0.0
    )

    assert status == "valid"
    assert reasons == []


def test_classify_bin_quality_caution():
    preprocessor = DataPreprocessor()

    status, reasons = preprocessor._classify_bin_quality(
        median_flux=1.0,
        median_snr=30.0,
        negative_fraction=0.0
    )

    assert status == "caution"
    assert "SNR below 50" in reasons


def test_classify_bin_quality_rejected():
    preprocessor = DataPreprocessor()

    status, reasons = preprocessor._classify_bin_quality(
        median_flux=1.0,
        median_snr=10.0,
        negative_fraction=0.0
    )

    assert status == "rejected"
    assert "SNR below 20" in reasons