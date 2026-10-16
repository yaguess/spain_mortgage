from dataclasses import dataclass, field
from typing import List


# ──────────────────────────────────────────────
# SUPUESTOS / INPUTS
# ──────────────────────────────────────────────

@dataclass
class Hipoteca:

    ltv: float = 0.70
    tipo_anual: float = 0.03
    años: int = 20
    itp: float=0.09
    valor_inmueble_inicial: float = 150_000.0

    @property
    def capital_deuda(self) -> float:
        return self.valor_inmueble_inicial * (self.ltv)
    
    @property
    def capital_equity(self) -> float:
        return self.valor_inmueble_inicial - self.capital_deuda
    
    @property
    def itp_a_pagar(self) -> float:
        return self.valor_inmueble_inicial * self.itp

    @property
    def capital_inicial_aportado(self) -> float:
        return (self.capital_equity
                + self.itp_a_pagar)

    @property
    def cuota_anual(self) -> float:
        return (
            self.capital_deuda * self.tipo_anual / 
            (1 - (1 + self.tipo_anual) ** -self.años)
        )

    def cuadro_amortizacion(self) -> List[dict]:
        saldo = self.capital_deuda
        tabla = []
        for i in range(1, self.años + 1):
            intereses = saldo * self.tipo_anual
            capital_amortizado = self.cuota_anual - intereses
            saldo -= capital_amortizado
            tabla.append(
                {
                    "año": i,
                    "intereses": intereses,
                    "capital_amortizado": capital_amortizado,
                    "saldo_vivo": max(saldo, 0.0),
                }
            )
        return tabla


@dataclass
class Supuestos:

    meses_alquilado_media: float = 11
    coste_oportunidad_capital: float = 0.05
    valor_calculo_amortizacion: float = 120_000.0
    tipo_irpf_alquiler: float = 0.19
    descuento_irpf_perdidas: float = 0.425
    impuesto_ganancias_capital: float = 0.19
    #ingresos
    renta_alquiler_mensual_inicial: float = 700.0

    #gastos
    gastos_mantenimiento_anual_inicial: float = 1_500.0
    seguro_impago_mensual_inicial: float = 28.0
    gastos_comunidad_mensual_inicial: float = 50.0
    ibi_y_otros_impuestos_anual: float = 500.0

    #inflación ingresos
    inflacion_ingresos_anual: float = 0.02

    #tasa crecimiento valor vivienda
    tasa_crecimiento_vivienda: float = 0.017

    #inflación gastos
    inflacion_gastos_anual: float = 0.02
    inflacion_impuestos: float = 0.01

    @property
    def renta_alquiler_anual_inicial(self) -> float:
        return self.renta_alquiler_mensual_inicial * 12 * (self.meses_alquilado_media / 12)

    @property
    def amortizacion_afa_anual(self) -> float:
        return self.valor_calculo_amortizacion * 0.03 * (self.meses_alquilado_media / 12)

    @property
    def gastos_comunidad_anual_inicial(self) -> float:
        return self.gastos_comunidad_mensual_inicial * 12

    @property
    def seguro_impago_anual_inicial(self) -> float:
        return self.seguro_impago_mensual_inicial * 12


# ──────────────────────────────────────────────
# RESULTADO POR AÑO
# ──────────────────────────────────────────────


@dataclass
class ResultadoAnual:
    año: int
    ingresos: float
    gastos_operativos: float
    intereses_hipoteca: float
    capital_amortizado: float
    saldo_vivo: float
    afa: float
    base_imponible: float
    impuestos: float
    cash_flow_bruto: float
    cash_flow_final: float
    cash_flow_descontado: float


# ──────────────────────────────────────────────
# FUNCIONES AUXILIARES (puras, fuera de la clase)
# ──────────────────────────────────────────────


def calcular_impuesto(
    base: float, tipo_irpf: float, descuento_perdidas: float
) -> float:
    if base < 0:
        return base * descuento_perdidas
    return base * tipo_irpf


def calcular_tv_neto(
    terminal_value: float,
    valor_inmueble_inicial: float,
    impuesto_ganancias_capital: float,
) -> float:
    plusvalia = max(terminal_value - valor_inmueble_inicial, 0)
    return terminal_value - plusvalia * impuesto_ganancias_capital


def calcular_moic(
    cash_flows: List[float],
    terminal_value_neto: float,
    capital_inicial_aportado: float,
    coste_oportunidad_capital: float,
    años: int,
) -> float:
    valor_futuro_flujos = sum(
        cash_flows[i] * (1 + coste_oportunidad_capital) ** (años - (i + 1))
        for i in range(len(cash_flows))
    )
    return (valor_futuro_flujos + terminal_value_neto) / capital_inicial_aportado


def calcular_irr(
    cash_flows: List[float],
    terminal_value_neto: float,
    capital_inicial_aportado: float,
    precision: float = 1e-6,
    max_iter: int = 1000,
) -> float:
    flujos = (
        [-capital_inicial_aportado]
        + cash_flows[:-1]
        + [cash_flows[-1] + terminal_value_neto]
    )

    def npv(r):
        return sum(cf / (1 + r) ** t for t, cf in enumerate(flujos))

    lo, hi = -0.5, 5.0
    for _ in range(max_iter):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < precision:
            break
    return ((lo + hi) / 2) * 100


def calculate_terminal_value(
    valor_inmueble_inicial: float, tasa_anual_crecimiento_vivienda: float, años: float
) -> float:
    return valor_inmueble_inicial * (1 + tasa_anual_crecimiento_vivienda) ** años


def calcular_wacc(peso_equity: float, coste_equity: float,
                  peso_deuda: float, coste_deuda: float,
                  tipo_impuesto: float) -> float:

    if not abs(peso_equity + peso_deuda - 1.0) < 1e-9:
        raise ValueError(
            f"peso_equity + peso_deuda debe ser 1.0, "
            f"got {peso_equity + peso_deuda:.4f}"
        )

    return (
        peso_equity * coste_equity
        + peso_deuda * coste_deuda * (1 - tipo_impuesto)
    )

# ──────────────────────────────────────────────
# MODELO PRINCIPAL
# ──────────────────────────────────────────────

@dataclass
class ModeloAlquiler:
    hipoteca: Hipoteca = field(default_factory=Hipoteca)
    supuestos: Supuestos = field(default_factory=Supuestos)
    resultados: List[ResultadoAnual] = field(default_factory=list, init=False)
    valor_npv: float = field(default=0.0, init=False)
    rentabilidad_irr: float = field(default=0.0, init=False)
    moic: float = field(default=0.0, init=False)

    @property
    def terminal_value(self) -> float:
        return calculate_terminal_value(
            self.hipoteca.valor_inmueble_inicial,
            self.supuestos.tasa_crecimiento_vivienda,
            self.hipoteca.años,
        )

    @property
    def terminal_value_neto(self) -> float:
        return calcular_tv_neto(
            terminal_value=self.terminal_value,
            valor_inmueble_inicial=self.hipoteca.valor_inmueble_inicial,
            impuesto_ganancias_capital=self.supuestos.impuesto_ganancias_capital,
        )
    @property
    def tasa_descuento(self) -> float:
        return calcular_wacc(
            peso_equity= 1- self.hipoteca.ltv,
            coste_equity=self.supuestos.coste_oportunidad_capital,
            peso_deuda=self.hipoteca.ltv,
            coste_deuda=self.hipoteca.tipo_anual,
            tipo_impuesto=self.supuestos.tipo_irpf_alquiler,
        )

    @property
    def cagr(self) -> float:
        return (self.moic ** (1 / self.hipoteca.años) - 1) * 100

    def calcular(self):
        self.resultados = []
        tabla_hip = self.hipoteca.cuadro_amortizacion()

        for i in range(1, self.hipoteca.años + 1):
            hip = tabla_hip[i - 1]

            ingresos = self.supuestos.renta_alquiler_anual_inicial * (
                1 + self.supuestos.inflacion_ingresos_anual
            ) ** (i - 1)
            gastos_mantenimiento = self.supuestos.gastos_mantenimiento_anual_inicial * (
                1 + self.supuestos.inflacion_gastos_anual
            ) ** (i - 1)
            seguro = self.supuestos.seguro_impago_anual_inicial * (
                1 + self.supuestos.inflacion_gastos_anual
            ) ** (i - 1)
            comunidad = self.supuestos.gastos_comunidad_anual_inicial * (
                1 + self.supuestos.inflacion_gastos_anual
            ) ** (i - 1)
            ibi_y_otros_impuestos = self.supuestos.ibi_y_otros_impuestos_anual * (
                1 + self.supuestos.inflacion_impuestos
            ) ** (i - 1)
            
            gastos_operativos = (
                gastos_mantenimiento
                + seguro
                + comunidad
                + self.supuestos.ibi_y_otros_impuestos_anual
            )
            base_imponible = (
                ingresos
                - gastos_operativos
                - hip["intereses"]
                - self.supuestos.amortizacion_afa_anual
            )
            impuestos = calcular_impuesto(
                base=base_imponible,
                tipo_irpf=self.supuestos.tipo_irpf_alquiler,
                descuento_perdidas=self.supuestos.descuento_irpf_perdidas,
            )
            cash_flow_bruto = ingresos - gastos_operativos - self.hipoteca.cuota_anual
            cash_flow_final = cash_flow_bruto - impuestos
            cash_flow_descontado = (
                cash_flow_final / (1 + self.tasa_descuento) ** i
            )
            self.resultados.append(
                ResultadoAnual(
                    año=i,
                    ingresos=round(ingresos, 2),
                    gastos_operativos=round(gastos_operativos, 2),
                    intereses_hipoteca=round(hip["intereses"], 2),
                    capital_amortizado=round(hip["capital_amortizado"], 2),
                    saldo_vivo=round(hip["saldo_vivo"], 2),
                    afa=round(self.supuestos.amortizacion_afa_anual, 2),
                    base_imponible=round(base_imponible, 2),
                    impuestos=round(impuestos, 2),
                    cash_flow_bruto=round(cash_flow_bruto, 2),
                    cash_flow_final=round(cash_flow_final, 2),
                    cash_flow_descontado=round(cash_flow_descontado, 2),
                )
            )

        tv_descontado = (
            self.terminal_value_neto
            / (1 + self.tasa_descuento) ** self.hipoteca.años
        )

        self.valor_npv = (
            sum(r.cash_flow_descontado for r in self.resultados)
            + tv_descontado
            - self.hipoteca.capital_inicial_aportado
        )
        self.rentabilidad_irr = calcular_irr(
            cash_flows=[r.cash_flow_final for r in self.resultados],
            terminal_value_neto=self.terminal_value_neto,
            capital_inicial_aportado=self.hipoteca.capital_inicial_aportado,
        )
        self.moic = calcular_moic(
            cash_flows=[r.cash_flow_final for r in self.resultados],
            terminal_value_neto=self.terminal_value_neto,
            capital_inicial_aportado=self.hipoteca.capital_inicial_aportado,
            coste_oportunidad_capital=self.supuestos.coste_oportunidad_capital,
            años=self.hipoteca.años,
        )
