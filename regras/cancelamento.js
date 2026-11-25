// Regra: se o contrato permite criar assinatura, deve existir forma de cancelar.
export default (paths) => {
  const chaves = Object.keys(paths || {});
  const ehAssinatura = (c) => /(assinatura|subscri|plano)/i.test(c);
  const criaAssinatura = chaves.some((c) => ehAssinatura(c) && paths[c].post);
  const cancela = chaves.some(
    (c) => /cancel/i.test(c) || (ehAssinatura(c) && paths[c].delete)
  );
  if (criaAssinatura && !cancela) {
    return [{ message: "O contrato permite criar assinatura, mas não define como cancelá-la (obstrução de cancelamento)." }];
  }
};
