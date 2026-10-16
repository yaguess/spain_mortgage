import pytest

from mortgage import (
    Hipoteca,
    Supuestos,
    calcular_impuesto,
    calcular_tv_neto,
    calcular_wacc,
)


def test_hipoteca_capital_and_cuota():
    hipoteca = Hipoteca(ltv=0.8, tipo_anual=0.03, años=20, valor_inmueble_inicial=200_000.0)

    assert hipoteca.capital == 160_000.0
    assert round(hipoteca.cuota_anual, 2) == 10_754.51


def test_supuestos_renta_y_amortizacion_afa():
    supuestos = Supuestos(meses_alquilado_media=10, valor_calculo_amortizacion=100_000.0)

    assert supuestos.renta_alquiler_anual_inicial == pytest.approx(700.0 * 12 * (10 / 12))
    assert supuestos.amortizacion_afa_anual == pytest.approx(100_000.0 * 0.03 * (10 / 12))


def test_calcular_impuesto():
    assert calcular_impuesto(1_000.0, 0.19, 0.425) == 190.0
    assert calcular_impuesto(-1_000.0, 0.19, 0.425) == -425.0


def test_calcular_tv_neto():
    terminal = 180_000.0
    assert calcular_tv_neto(terminal, 150_000.0, 0.425) == pytest.approx(
        180_000.0 - (180_000.0 - 150_000.0) * 0.425
    )


def test_calcular_wacc():
    wacc = calcular_wacc(0.5, 0.1, 0.5, 0.04, 0.25)
    assert wacc == pytest.approx(0.5 * 0.1 + 0.5 * 0.04 * (1 - 0.25))


def test_calcular_wacc_invalid_weights():
    with pytest.raises(ValueError):
        calcular_wacc(0.4, 0.1, 0.4, 0.04, 0.25)
