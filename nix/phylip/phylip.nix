{ stdenv }:

stdenv.mkDerivation {
  pname = "phylip";
  version = "3.698";

  src = fetchTarball {
    url = "https://phylipweb.github.io/phylip/download/phylip-3.697.tar.gz";
    sha256 = "sha256-u6M3VyBNRKPRDuqz9dzsNkaYbsdqWgioThK2lWiL6Vg=";
  };

  NIX_CFLAGS_COMPILE = "-fcommon -std=gnu89";

  buildPhase = ''
    cd src
    make -f Makefile.unx all
  '';

  installPhase = ''
    find . -maxdepth 1 -type f -executable
    mkdir -p $out/bin
    mv clique $out/bin/clique
    mv consense $out/bin/consense
    mv contml $out/bin/contml
    mv contrast $out/bin/contrast
    mv dnacomp $out/bin/dnacomp
    mv dnadist $out/bin/dnadist
    mv dnainvar $out/bin/dnainvar
    mv dnaml $out/bin/dnaml
    mv dnamlk $out/bin/dnamlk
    mv dnamove $out/bin/dnamove
    mv dnapars $out/bin/dnapars
    mv dnapenny $out/bin/dnapenny
    mv dolmove $out/bin/dolmove
    mv dollop $out/bin/dollop
    mv dolpenny $out/bin/dolpenny
    mv factor $out/bin/factor
    mv fitch $out/bin/fitch
    mv gendist $out/bin/gendist
    mv kitsch $out/bin/kitsch
    mv mix $out/bin/mix
    mv move $out/bin/move
    mv neighbor $out/bin/neighbor
    mv pars $out/bin/pars
    mv penny $out/bin/penny
    mv proml $out/bin/proml
    mv promlk $out/bin/promlk
    mv protdist $out/bin/protdist
    mv protpars $out/bin/protpars
    mv restdist $out/bin/restdist
    mv restml $out/bin/restml
    mv retree $out/bin/retree
    mv seqboot $out/bin/seqboot
    mv treedist $out/bin/treedist
    mv drawgram $out/bin/drawgram
    mv drawtree $out/bin/drawtree

  '';

}
