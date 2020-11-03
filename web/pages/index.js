import React, {useState, useEffect, useRef} from 'react';
import PropTypes from 'prop-types';
import Layout from '../components/Layout';
import {useTheme} from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';

import useMediaQuery from '@material-ui/core/useMediaQuery';
import Dialog from '@material-ui/core/Dialog';
import DialogActions from '@material-ui/core/DialogActions';
import DialogContent from '@material-ui/core/DialogContent';
import DialogTitle from '@material-ui/core/DialogTitle';

import Counter from '../src/api/counter';
import promiseToCallback from 'higher-order-helper/promiseToCallback';

import IconButton from '@material-ui/core/IconButton';
import DeleteIcon from '@material-ui/icons/Delete';
import EditIcon from '@material-ui/icons/Edit';
import AddIcon from '@material-ui/icons/Add';
import RemoveIcon from '@material-ui/icons/Remove';
import Chip from '@material-ui/core/Chip';

import styles from '../styles/Home.module.css';

function RealCounter({user, counter: info, onEdit, onDestory}) {
  const counter = new Counter(user, info);
  const [count, setCount] = useState(info.count);
  function updateCount(step) {
    promiseToCallback(counter.incr.bind(counter))(step, '', (err, result) => {
      setCount(count + step);
    });
  }
  return (
    <div className={styles.card}>
      <h3>{info.name}</h3>
      <div className={styles['card-action']}>
        <IconButton aria-label="edit" size="small" onClick={() => onEdit()}>
          <EditIcon fontSize="small" />
        </IconButton>
        <IconButton aria-label="delete" size="small"
          onClick={() => onDestory()}>
          <DeleteIcon fontSize="small" />
        </IconButton>
      </div>
      <div className={styles.counter}>
        <IconButton aria-label="remove" onClick={() => updateCount(-1)}>
          <RemoveIcon />
        </IconButton>
        <Chip label={count} color="primary"
          className={styles['counter-count']} />
        <IconButton aria-label="add" onClick={() => updateCount(1)}>
          <AddIcon />
        </IconButton>
      </div>
      <p>{info.remark}</p>
    </div>
  );
}

RealCounter.propTypes = {
  user: PropTypes.object.required,
  counter: PropTypes.object.required,
  onEdit: PropTypes.func,
  onDestory: PropTypes.func,
};


function Home(props) {
  const user = props.user;
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down('sm'));

  const [openAddDia, setOpenAddDia] = useState(false);
  const [name, setName] = useState('');
  const [remark, setRemark] = useState('');
  const [errors, setErrors] = useState({});
  const [cid, setCid] = useState(0);
  const [updated, setUpdated] = useState(false);

  function handleEdit(counter) {
    setName(counter.name);
    setRemark(counter.remark);
    setCid(counter.id);
    setOpenAddDia(true);
  }

  function handleSave() {
    let hasErr = false;
    const errors = {};
    if (!name) {
      errors.name = '请输入计数器名称';
      hasErr = true;
    }

    if (hasErr) {
      setErrors({errors});
      return;
    }
    function cleanUp() {
      setOpenAddDia(false);
      setName('');
      setRemark('');
      setCid(0);
      setUpdated(!updated);
    }
    if (cid > 0) {
      const counter = new Counter(user, {id: cid});
      promiseToCallback(counter.update.bind(counter))({name, remark}, (err) => {
        if (err) {
          alert('保存失败');
          return;
        }
        cleanUp();
      });
    } else {
      promiseToCallback(user.createCounter.bind(user))(name, remark,
        (err, counter) => {
          if (err) {
            alert('添加失败');
            return;
          }
          cleanUp();
        });
    }
  }

  function handleDestory(info) {
    if (!confirm('确定删除计数器！')) {
      return;
    }
    const counter = new Counter(user, info);
    promiseToCallback(counter.destory.bind(counter))((err) => {
      if (err) {
        alert('删除失败');
        return;
      }
      setUpdated(!updated);
    });
  }

  const [counters, setCounters] = useState([]);
  const [offset, setOffset] = useState(0);
  const fetchRequestRef = useRef();

  function fetchCounters() {
    const id = Date.now();
    fetchRequestRef.current = id;
    promiseToCallback(user.getCounterList.bind(user))({offset, size: 10},
      (err, res) => {
        if (fetchRequestRef.current !== id) {
          return;
        }
        if (err) {
          console.log(err);
        } else {
          setOffset(res.offset);
          setCounters(res.counters);
        }
      });
  }

  useEffect(fetchCounters, [offset, updated]);

  return (
    <Layout title='计数器' {...props}>
      <main className={styles.main}>
        <div className={styles.grid}>
          <div className={styles.card + ' ' + styles['add-counter']}>
            <IconButton aria-label="add" size='medium'
              onClick={() => setOpenAddDia(true)}>
              <AddIcon className={styles['new-counter']} fontSize='large'/>
            </IconButton>
          </div>
          {counters.map((counter) =>
            <RealCounter counter={counter} user={user}
              onEdit={() => handleEdit(counter)}
              onDestory={() => handleDestory(counter)} key={counter.id} />)}
        </div>
        <Dialog
          fullScreen={fullScreen}
          open={openAddDia}
          onClose={() => setOpenAddDia(false)}
          aria-labelledby="responsive-dialog-title"
        >
          <DialogTitle id="responsive-dialog-title">
            {cid > 0 ? '编辑计数器' : '添加计数器'}
          </DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="计数器名称"
              type="text"
              fullWidth
              value={name}
              onChange={({target}) => {
                setName(target.value);
                setErrors({...errors, name: null});
              }}
            />
            <TextField
              margin="dense"
              label="简要描述"
              type="text"
              fullWidth
              value={remark}
              onChange={({target}) => {
                setRemark(target.value);
                setErrors({...errors, remark: null});
              }}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={handleSave} color="primary">
              保存
            </Button>
          </DialogActions>
        </Dialog>
      </main>
    </Layout>
  );
}

Home.requireLogin = true;

Home.propTypes = {
  user: PropTypes.object.required,
};

export default Home;
