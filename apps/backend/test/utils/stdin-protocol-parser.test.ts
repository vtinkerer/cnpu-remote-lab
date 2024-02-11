import test from 'ava';
import { StdinProtocolParser } from '../../src/utils/stdin-protocol-parser';

const DELIMITER = '<DELIM>';

const createParser = () => {
  return { parser: new StdinProtocolParser(DELIMITER) };
};

test('it parses the full message in one string', async (t) => {
  const { parser } = createParser();

  const message = 'hello';

  parser.on('data', (data) => {
    t.is(data, message);
  });

  parser.process(message + DELIMITER);
});

test('it doesnt emit data when the message is not complete', async (t) => {
  const { parser } = createParser();

  const message = 'hello';

  parser.on('data', () => {
    t.fail();
  });

  parser.process(message);
  t.pass();
});

test('it emits the data two times when the input contains two full messages', async (t) => {
  const { parser } = createParser();

  const message1 = 'hello';
  const message2 = 'world';

  let count = 0;
  parser.on('data', (data) => {
    if (count === 0) {
      t.is(data, message1);
    } else if (count === 1) {
      t.is(data, message2);
    }
    count++;
  });

  parser.process(message1 + DELIMITER + message2 + DELIMITER);
  t.is(count, 2);
});

test('it emits the data two times when the input contains two full messages and a partial message', async (t) => {
  const { parser } = createParser();

  const message1 = 'hello';
  const message2 = 'world';
  const message3 = 'partial';

  let count = 0;
  parser.on('data', (data) => {
    if (count === 0) {
      t.is(data, message1);
    } else if (count === 1) {
      t.is(data, message2);
    }
    count++;
  });

  parser.process(message1 + DELIMITER + message2 + DELIMITER + message3);
  t.is(count, 2);
});

test('it emits the data if the message is split in three', async (t) => {
  const { parser } = createParser();

  const part1 = 'hello';
  const part2 = ' my';
  const part3 = ' friend';

  parser.on('data', (data) => {
    t.is(data, part1 + part2 + part3);
  });

  parser.process(part1);
  parser.process(part2);
  parser.process(part3 + DELIMITER);
});

test('it emits the data two times if there are two messages split into three inputs', async (t) => {
  const { parser } = createParser();

  const part1 = 'hello';
  const part2 = ' my';

  const part3 = ' friend';
  const part4 = 'how';

  const part5 = ' are';
  const part6 = ' you';

  let count = 0;
  parser.on('data', (data) => {
    if (count === 0) {
      t.is(data, part1 + part2 + part3);
    } else if (count === 1) {
      t.is(data, part4 + part5 + part6);
    }
    count++;
  });

  parser.process(part1 + part2);
  parser.process(part3 + DELIMITER + part4);
  parser.process(part5 + part6 + DELIMITER);
  t.is(count, 2);
});
